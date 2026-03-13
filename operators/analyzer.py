import bpy
from .. import utils
import json

class LOD_OT_CollectionAnalyzer(bpy.types.Operator):
    """Analyzes collection vertex counts and color-codes them"""
    bl_idname = "lod.collectionanalyzer"
    bl_label = "Run Analyzer"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        scn = context.scene.lod_props
        
        # 1. 强制清理旧状态
        bpy.ops.lod.cleancolors()

        self.report({'INFO'}, "Analyzing Collections...")
        
        # 2. 获取参数
        if scn.colA_Method == 'm1':
            m_vhigh, m_high, m_med, m_low = 0.9, 0.8, 0.6, 0.2
        else:
            m_vhigh = scn.mult_veryhigh
            m_high = scn.mult_high
            m_med = scn.mult_medium
            m_low = scn.mult_low

        backup = {}
        scene_total_verts = 0
        max_col_verts = 0
        use_heatmap = scn.CA_use_heatmap  # 是否使用热力图颜色

        # 3. 统计全场景
        for obj in context.view_layer.objects:
            if obj.type == 'MESH':
                 scene_total_verts += len(obj.data.vertices) # 简单统计，为了速度
        
        if scene_total_verts == 0: scene_total_verts = 1 # 防止除以0

        # 4. 遍历集合
        for col in bpy.data.collections:
            # 备份原始颜色（无论是否使用热力图都需要备份，以便还原名称时使用）
            backup[col.name] = col.color_tag
            
            # 只在使用热力图模式时重置颜色
            if use_heatmap:
                col.color_tag = 'NONE' # 重置

            # 计算该集合顶点数
            v_count = utils.get_collection_vertex_count(col)
            if v_count > max_col_verts: max_col_verts = v_count

            # 只有当集合有东西时才处理
            if v_count > 0:
                # 4.1 重命名：增加百分比后缀
                percent = (v_count / scene_total_verts) * 100.0
                col.name = f"{col.name} | {percent:.1f}%"

                # 4.2 颜色判定（仅在启用热力图时）
                if use_heatmap:
                    # 假设基准：如果占场景总量的比例超过阈值
                    ratio = v_count / scene_total_verts
                    
                    # 这里稍微调整逻辑以适应滑块：
                    # 如果我们把滑块当做百分比阈值 (0.9 = 90% vertices)
                    if ratio >= m_vhigh: col.color_tag = 'COLOR_01'   # Red
                    elif ratio >= m_high: col.color_tag = 'COLOR_02'  # Orange
                    elif ratio >= m_med: col.color_tag = 'COLOR_03'   # Yellow
                    elif ratio >= m_low: col.color_tag = 'COLOR_04'   # Green
                    else: col.color_tag = 'COLOR_05'                  # Blue

        # 保存备份
        scn.default_col_colors = json.dumps(backup)
        scn.CA_Toggle = True 
        return {'FINISHED'}

class LOD_OT_CleanColors(bpy.types.Operator):
    """Restores original collection names and colors"""
    bl_idname = "lod.cleancolors"
    bl_label = "Clear Analyzer"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        scn = context.scene.lod_props
        
        # 读取备份
        data = {}
        if scn.default_col_colors:
            try: 
                #  使用 json.loads 替代 eval()，移除安全隐患
                data = json.loads(scn.default_col_colors)
            except Exception as e:
                print(f"LODify Error loading colors: {e}")
                pass

        for col in bpy.data.collections:
            # 1. 先提取基础名称 (去除 " | 10.5%" 这种后缀)
            base_name = col.name.split(' | ')[0].strip() if ' | ' in col.name else col.name
            
            # 2. 还原颜色（使用基础名称查找备份）
            if base_name in data:
                col.color_tag = data[base_name]
            
            # 3. 还原名字
            if ' | ' in col.name:
                col.name = base_name

        scn.CA_Toggle = False
        scn.default_col_colors = ""
        return {'FINISHED'}

# ... (ViewAnalyzer Code stays roughly the same) ...
class LOD_OT_ViewAnalyzer(bpy.types.Operator):
    """Analyzes objects in 3D view and color-codes by density"""
    bl_idname = "lod.viewanalyzer"
    bl_label = "Run 3D View Analyzer"


    def execute(self, context):
        scn = context.scene.lod_props
        if context.space_data.type == 'VIEW_3D':
            scn.last_shading = context.space_data.shading.color_type
            context.space_data.shading.type = 'SOLID'
            context.space_data.shading.color_type = 'OBJECT'
        
        # 简单染色逻辑
        max_v = 1
        mesh_objs = [o for o in context.view_layer.objects if o.type == 'MESH']
        for o in mesh_objs:
            if len(o.data.vertices) > max_v: max_v = len(o.data.vertices)
        
        from mathutils import Color
        for o in mesh_objs:
            # 备份原始颜色
            if "_lod_orig_color" not in o:
                o["_lod_orig_color"] = list(o.color)
            
            ratio = len(o.data.vertices) / max_v
            # 红色(Hue 0)到蓝色(Hue 0.66)
            c = Color()
            c.hsv = (0.66 * (1.0 - ratio), 1.0, 1.0)
            o.color = (c.r, c.g, c.b, 1.0)

        scn.AA_Toggle = True
        return {'FINISHED'}

class LOD_OT_CleanViewAnalyzer(bpy.types.Operator):
    """Clear View Analyzer"""
    bl_idname = "lod.cleanviewanalyzer"
    bl_label = "Clear View Analyzer"

    
    def execute(self, context):
        scn = context.scene.lod_props
        if context.space_data.type == 'VIEW_3D':
            target = scn.last_shading if scn.last_shading else 'MATERIAL'
            context.space_data.shading.color_type = target
        
        # 恢复物体原始颜色
        for o in context.view_layer.objects:
            if "_lod_orig_color" in o:
                try:
                    o.color = tuple(o["_lod_orig_color"])
                except:
                    o.color = (1, 1, 1, 1)
                del o["_lod_orig_color"]

        scn.AA_Toggle = False
        return {'FINISHED'}



classes = (
    LOD_OT_CollectionAnalyzer,
    LOD_OT_CleanColors, 
    LOD_OT_ViewAnalyzer,
    LOD_OT_CleanViewAnalyzer,
        )

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
