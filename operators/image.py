import os
import re
import bpy
import shutil
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
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Please save the .blend file first!")
            return {'CANCELLED'}

        # 获取目标尺寸
        if scn.resize_size == 'c':
            target_size = scn.custom_resize_size
        else:
            target_size = int(scn.resize_size)

        # --- [逻辑修改] 动态生成文件夹名称 ---
        folder_name = f"textures_{target_size}px" 
        
        # 决定最终路径
        if scn.duplicate_images and not scn.use_same_directory:
            # 如果用户指定了自定义路径，就在自定义路径下创建 textures_1024px
            output_dir = os.path.join(bpy.path.abspath(scn.custom_output_path), folder_name)
        else:
            # 默认在 blend 文件旁边的 textures_1024px
            output_dir = os.path.join(base_path, folder_name)

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.report({'ERROR'}, f"Cannot create directory: {e}")
                return {'CANCELLED'}

        resized_count = 0
        
        for item in scn.image_list:
            if not item.image_selected: continue

            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue
            
            # 即使原图比目标小，为了统一管理，建议也处理，或者你可以保留这个判断
            if img.size[0] <= target_size and img.size[1] <= target_size:
                # continue # 如果你想跳过小图，取消注释
                pass 

            try:
                # 0. 记录原始路径
                if "tot_original_path" not in img:
                    img["tot_original_path"] = img.filepath
                # 1. 构造文件名
                original_filepath = img.filepath_from_user()
                file_name = os.path.basename(original_filepath)
                if not file_name: file_name = f"{img.name}.png"
                
                name_part, ext_part = os.path.splitext(file_name)
                if not ext_part: ext_part = ".png"
                
                # 新文件名: my_texture_1024px.jpg
                new_file_name = f"{name_part}_{target_size}px{ext_part}"
                new_full_path = os.path.join(output_dir, new_file_name)
                
                # 2. 内存缩放
                img.scale(target_size, target_size)
                
                # 3. 物理保存
                img.save_render(filepath=new_full_path)
                
                # 4. 重连并刷新
                img.filepath = new_full_path
                img.reload()
                
                resized_count += 1

            except Exception as e:
                self.report({'ERROR'}, f"Error processing {img.name}: {e}")

        # 刷新列表
        bpy.ops.tot.updateimagelist()
        
        # 强制刷新 UI (为了让 Clean Up 面板立马显示新文件夹)
        context.area.tag_redraw()
        
        self.report({'INFO'}, f"Optimized {resized_count} textures into folder: {folder_name}")
        return {'FINISHED'}

class TOT_OT_ClearDuplicateImage(bpy.types.Operator):
    """清理重复贴图：将 .001, .002 结尾的图片替换为原始图片"""
    bl_idname = "tot.clearduplicateimage"
    bl_label = "Clear Duplicate Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cleaned_count = 0
        
        # 1. 建立映射表：{"Image.001": "Image", "Texture.002": "Texture"}
        # 仅当不带后缀的原始图片存在时才进行替换
        remap_dict = {} # Key: Duplicate Name, Value: Original Image Object
        
        # 获取所有图片
        all_images = list(bpy.data.images)
        
        for img in all_images:
            # 检查名字是否类似 "Name.001"
            if len(img.name) > 4 and img.name[-4] == '.' and img.name[-3:].isdigit():
                base_name = img.name[:-4] # 移除后缀
                
                # 查找是否存在原始图片
                original_img = bpy.data.images.get(base_name)
                
                # 只有当原始图片存在，且不是同一个对象时
                if original_img and original_img != img:
                    # 也可以加一层校验：比如文件路径是否一致，防止误杀同名不同图
                    # 这里简化逻辑：名字匹配即替换
                    remap_dict[img.name] = original_img

        if not remap_dict:
            self.report({'INFO'}, "No duplicate images found.")
            return {'FINISHED'}

        # 2. 遍历所有材质，替换节点中的引用
        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree: continue
            
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    if node.image.name in remap_dict:
                        target_img = remap_dict[node.image.name]
                        print(f"Swapping {node.image.name} -> {target_img.name} in material {mat.name}")
                        node.image = target_img
                        cleaned_count += 1
                        
        # 3. 清理未使用的图片 (可选：purge)
        # 这里为了安全，只替换引用，不做 purge，用户可以手动 File -> Clean Up -> Unused Data Blocks
        
        # 刷新列表
        bpy.ops.tot.updateimagelist()
        
        self.report({'INFO'}, f"Replaced {cleaned_count} duplicate image references.")
        return {'FINISHED'}

class TOT_OT_DeleteTextureFolder(bpy.types.Operator):
    """删除指定的贴图文件夹 (物理删除)"""
    bl_idname = "tot.delete_texture_folder"
    bl_label = "Delete Folder"
    bl_options = {'REGISTER', 'UNDO'} # 注意：文件删除无法通过 Blender 的 Undo 撤销

    folder_name: bpy.props.StringProperty() # 接收参数

    def execute(self, context):
        base_path = bpy.path.abspath("//")
        if not base_path: return {'CANCELLED'}
        
        target_path = os.path.join(base_path, self.folder_name)
        
        if os.path.exists(target_path):
            try:
                # 危险操作：删除整个文件夹树
                shutil.rmtree(target_path)
                self.report({'INFO'}, f"Deleted folder: {self.folder_name}")
                
                # 强制刷新 UI
                context.area.tag_redraw()
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete: {e}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Folder not found.")
            
        return {'FINISHED'}

    def invoke(self, context, event):
        # 弹窗确认，防止误删
        return context.window_manager.invoke_confirm(self, event)

class TOT_OT_SwitchResolution(bpy.types.Operator):
    """在原图和不同分辨率的缓存图之间切换"""
    bl_idname = "tot.switch_resolution"
    bl_label = "Switch Texture Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    # 接收目标分辨率参数，'ORIGINAL' 代表原图
    target_res: bpy.props.StringProperty() 

    def execute(self, context):
        scn = context.scene.tot_props
        target = self.target_res
        
        base_path = bpy.path.abspath("//")
        switched_count = 0
        missing_count = 0

        for item in scn.image_list:
            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue

            # --- 切换回原图 ---
            if target == 'ORIGINAL':
                # 如果有存档记录，就恢复
                if "tot_original_path" in img:
                    orig_path = img["tot_original_path"]
                    # 检查原图是否存在 (防止用户删了原图)
                    abs_orig_path = bpy.path.abspath(orig_path)
                    if os.path.exists(abs_orig_path):
                        img.filepath = orig_path
                        img.reload()
                        switched_count += 1
                    else:
                        print(f"Original file missing: {abs_orig_path}")
                        missing_count += 1
                else:
                    # 如果没有存档，说明这张图可能从未被缩放过，保持原样
                    pass

            # --- 切换到指定分辨率 (如 1024) ---
            else:
                # 1. 确定文件夹: textures_1024px
                folder_name = f"textures_{target}px"
                search_dir = os.path.join(base_path, folder_name)
                
                # 2. 推断目标文件名
                # 难点：当前 img.filepath 可能是原名，也可能是 xxx_2048px.png
                # 我们需要找到 "干净的" 基础名
                current_filename = os.path.basename(img.filepath)
                name_base, ext = os.path.splitext(current_filename)
                
                # 清洗文件名：如果当前文件名包含 _128px, _1024px 等，把它剥离
                # 简单的做法是：如果有存档，用存档的文件名来推断
                if "tot_original_path" in img:
                    clean_name = os.path.basename(img["tot_original_path"])
                    name_base, ext = os.path.splitext(clean_name)
                else:
                    # 如果没有存档，尝试智能剥离 (假设格式是 name_NUMpx)
                    import re
                    # 移除结尾的 _1234px
                    name_base = re.sub(r'_\d+px$', '', name_base)

                # 构造目标路径: textures_1024px/name_1024px.png
                target_filename = f"{name_base}_{target}px{ext}"
                target_full_path = os.path.join(search_dir, target_filename)

                # 3. 检查文件是否存在
                if os.path.exists(target_full_path):
                    img.filepath = target_full_path
                    img.reload()
                    switched_count += 1
                else:
                    # 对应的缩放图不存在（可能没生成过）
                    pass
        
        # 刷新列表更新大小显示
        bpy.ops.tot.updateimagelist()
        
        if target == 'ORIGINAL':
            self.report({'INFO'}, f"Restored {switched_count} images to Original.")
        else:
            self.report({'INFO'}, f"Switched {switched_count} images to {target}px.")
            
        return {'FINISHED'}

classes = (
    TOT_OT_UpdateImageList,
    TOT_OT_SelectAllImages,
    TOT_OT_ResizeImages,
    TOT_OT_ClearDuplicateImage,
    TOT_OT_DeleteTextureFolder,
    TOT_OT_SwitchResolution,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)