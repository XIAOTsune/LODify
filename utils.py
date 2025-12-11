import bpy

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