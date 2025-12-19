import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

def calculate_screen_coverage(scene, obj, camera):
    """
    计算物体在相机视角下的屏幕占比（像素宽度估算）。
    返回: (max_width_pixels, is_visible)
    """
    if not camera or not obj:
        return 0, False

    # 获取渲染分辨率
    render = scene.render
    res_x = render.resolution_x
    res_y = render.resolution_y
    scale = render.resolution_percentage / 100.0
    
    real_x = res_x * scale
    real_y = res_y * scale
    
    # 获取物体包围盒的 8 个顶点（世界坐标）
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    min_x, max_x = 1.0, 0.0
    min_y, max_y = 1.0, 0.0
    in_front = False

    # 将所有顶点投影到 2D 屏幕空间 (0.0 ~ 1.0)
    for corner in bbox_corners:
        co_2d = world_to_camera_view(scene, camera, corner)
        
        # co_2d.z 是深度，负数表示在相机背后
        if co_2d.z > 0:
            in_front = True
            min_x = min(min_x, co_2d.x)
            max_x = max(max_x, co_2d.x)
            min_y = min(min_y, co_2d.y)
            max_y = max(max_y, co_2d.y)
    
    # 如果所有点都在相机背后，或者物体在视野外
    if not in_front:
        return 0, False
        
    # 计算 2D 包围盒的宽高
    width = max(0.0, max_x - min_x)
    height = max(0.0, max_y - min_y)
    
    # 简单的视锥剔除：如果完全在画面外 (比如 x > 1 或 x < 0)
    # 这里做个宽松判断，因为 min_x 可能 < 0 但 max_x > 0 (跨越边界)
    if max_x < 0 or min_x > 1 or max_y < 0 or min_y > 1:
        # 虽然在相机前方，但在视锥体外面
        return 0, False

    # 转换为像素值
    pixel_width = width * real_x
    pixel_height = height * real_y
    
    # 取最长边作为分辨率参考
    return max(pixel_width, pixel_height), True

def get_normalized_screen_ratio(scene, obj, camera):
    """
    获取归一化的屏幕占比 (0.0 ~ 1.0)
    Ratio = 物体屏幕最长边像素 / 屏幕渲染长边像素
    """
    pixels, visible = calculate_screen_coverage(scene, obj, camera)
    if not visible:
        return 0.0
    
    render = scene.render
    # 取屏幕长宽的最大值作为分母
    max_screen_res = max(render.resolution_x, render.resolution_y)
    
    if max_screen_res == 0: return 0.0
    
    return min(pixels / max_screen_res, 1.0)

def get_stepped_lod_factor(raw_ratio, min_protection=0.01):
    """
    LOD 阶梯映射策略
    根据设计方案将连续的 Ratio 离散化为固定的 Factor
    """
    target_factor = 1.0
    
    # 阶梯表
    if raw_ratio > 0.8:     # 极高
        target_factor = 1.0
    elif raw_ratio > 0.5:   # 高
        target_factor = 0.7
    elif raw_ratio > 0.2:   # 中
        target_factor = 0.4
    elif raw_ratio > 0.05:  # 低
        target_factor = 0.1
    else:                   # 极低
        target_factor = 0.01 # 或者 0.0，视情况而定
        
    # 应用最小保护值 (Min Ratio)
    # 如果计算出的 target_factor 比用户设置的底限还要低，则提升至底限
    # 但如果 target_factor 本来就是 1.0 (全屏)，则不需要降低
    return max(target_factor, min_protection)

def get_collection_vertex_count(collection):
    """递归计算集合内所有 Mesh 对象的顶点总数"""
    total_verts = 0
    # 遍历集合内的所有对象
    for obj in collection.all_objects:
        if obj.type == 'MESH' and obj.data:
            total_verts += len(obj.data.vertices)
    return total_verts

def get_image_size_str(image):
    """估算图片占用的内存大小 (MB)"""
    if not image:
        return "0.00"
    
    try:
        width = image.size[0]
        height = image.size[1]
        # 估算：宽 * 高 * 4通道 (RGBA) * 深度 (通常 32bit float 或 8bit byte)
        # 这里简化按未压缩的 RGBA 8bit 估算，或者 32bit float
        # Blender 内部通常是 32bit float (4 bytes per channel)
        bytes_size = width * height * 4 * 4 
        size_mb = bytes_size / (1024 * 1024)
        return f"{size_mb:.2f}"
    except:
        return "0.00"

def format_large_number(num):
    """将大数字格式化为 K/M 后缀"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)
    
    # ... (保留原有的引用和函数) ...

def get_instance_sources(scene):
    """
    扫描场景，找出所有被用作“实例源”的物体。
    包括：粒子系统的发射物体、几何节点中引用的物体/集合。
    """
    sources = set()
    
    # 遍历场景中所有物体进行检查
    for obj in scene.objects:
        
        # 1. 检查粒子系统 (Particle Systems)
        if len(obj.particle_systems) > 0:
            for ps in obj.particle_systems:
                settings = ps.settings
                # 物体模式
                if settings.render_type == 'OBJECT' and settings.instance_object:
                    sources.add(settings.instance_object)
                # 集合模式
                elif settings.render_type == 'COLLECTION' and settings.instance_collection:
                    for member in settings.instance_collection.all_objects:
                        sources.add(member)

        # 2. 检查几何节点 (Geometry Nodes)
        # 注意：这需要遍历节点树，可能会有一点点慢，但在 Setup 阶段是可以接受的
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                try:
                    # 遍历节点寻找 Object Info 和 Collection Info
                    for node in mod.node_group.nodes:
                        # Object Info 节点
                        if node.type == 'OBJECT_INFO':
                            # 输入接口通常第一个是 Object
                            target = node.inputs[0].default_value 
                            if target:
                                sources.add(target)
                        
                        # Collection Info 节点
                        elif node.type == 'COLLECTION_INFO':
                            target_col = node.inputs[0].default_value
                            if target_col:
                                for member in target_col.all_objects:
                                    sources.add(member)
                except:
                    pass
                    
    return sources