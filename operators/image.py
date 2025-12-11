import bpy
from .. import utils # 导入工具

class TOT_OT_UpdateImageList(bpy.types.Operator):
    bl_idname = "tot.updateimagelist"
    bl_label = "Update Image List"
    
    def execute(self, context):
        scn = context.scene.tot_props
        scn.image_list.clear()
        
        total_size_mb = 0.0
        count = 0
        
        for img in bpy.data.images:
            # 排除渲染结果和浏览器节点
            if img.name in {'Render Result', 'Viewer Node'}: continue
            # 排除生成的图片 (Generated) 通常不需要压缩
            if img.source == 'GENERATED': continue

            item = scn.image_list.add()
            item.tot_image_name = img.name
            
            # 状态检查
            if img.packed_file:
                item.packed_img = 1 # Packed
            elif img.library:
                item.packed_img = 2 # Linked
            else:
                item.packed_img = 0 # File
            
            # 计算大小
            size_str = utils.get_image_size_str(img)
            item.image_size = size_str
            total_size_mb += float(size_str)
            
            count += 1
            
        scn.r_total_images = count
        scn.total_image_memory = f"{total_size_mb:.2f}"
        
        return {'FINISHED'}

class TOT_OT_SelectAllImages(bpy.types.Operator):
    bl_idname = "tot.imglistselectall"
    bl_label = "Select All"
    
    def execute(self, context):
        scn = context.scene.tot_props
        # 智能反选
        has_unselected = any(not i.image_selected for i in scn.image_list)
        for i in scn.image_list:
            i.image_selected = has_unselected
        return {'FINISHED'}

class TOT_OT_ResizeImages(bpy.types.Operator):
    bl_idname = "tot.resizeimages"
    bl_label = "Resize Images"
    
    def execute(self, context):
        scn = context.scene.tot_props
        
        # 获取目标尺寸
        if scn.resize_size == 'c':
            target_size = scn.custom_resize_size
        else:
            target_size = int(scn.resize_size)

        resized_count = 0
        
        # 遍历 UI 列表
        for item in scn.image_list:
            if item.image_selected:
                img = bpy.data.images.get(item.tot_image_name)
                if not img: continue
                
                # 只有当图片大于目标尺寸时才缩小
                if img.size[0] > target_size or img.size[1] > target_size:
                    try:
                        # 缩放逻辑
                        img.scale(target_size, target_size)
                        
                        # !注意!：如果是外部文件，Blender 不会自动保存覆盖原图
                        # 如果是 Packed 图片，数据已经改变
                        
                        self.report({'INFO'}, f"Resized: {img.name}")
                        resized_count += 1
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to resize {img.name}: {e}")

        # 刷新列表显示最新大小
        bpy.ops.tot.updateimagelist()
        
        self.report({'INFO'}, f"Completed! Resized {resized_count} images.")
        return {'FINISHED'}

class TOT_OT_ClearDuplicateImage(bpy.types.Operator):
    bl_idname = "tot.clearduplicateimage"
    bl_label = "Clear Duplicate Images"

    def execute(self, context):
        # 简单的去重逻辑：如果名字是以 .001, .002 结尾，尝试查找无后缀的原名
        # 并替换用户的引用
        # 这里仅作占位，实际去重逻辑比较复杂，建议先保留空壳或简单打印
        self.report({'INFO'}, "Feature coming soon: Duplicate Cleaner")
        return {'FINISHED'}

classes = (
    TOT_OT_UpdateImageList,
    TOT_OT_SelectAllImages,
    TOT_OT_ResizeImages,
    TOT_OT_ClearDuplicateImage,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)