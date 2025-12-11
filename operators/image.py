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
        
        # 获取当前 blend 文件的绝对目录 (e.g. C:\Project\)
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}

        switched_count = 0
        
        for item in scn.image_list:
            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue
            
            # --- 情况 A: 切换回原图 ---
            if target == 'ORIGINAL':
                # 只有当图片有“存档记录”时才能恢复
                if "tot_original_path" in img:
                    orig_path = img["tot_original_path"]
                    
                    # 检查文件是否还在
                    # 注意：存档的路径通常是相对路径 (//Texture/abc.jpg)，需要转绝对路径检查
                    abs_orig_path = bpy.path.abspath(orig_path)
                    
                    if os.path.exists(abs_orig_path):
                        img.filepath = orig_path
                        img.reload()
                        switched_count += 1
                    else:
                        print(f"[TOT] Original file missing: {abs_orig_path}")
                else:
                    # 没有存档，说明它本身就是原图，或者从未被本插件处理过
                    pass

            # --- 情况 B: 切换到指定分辨率 (如 1024) ---
            else:
                # 1. 获取“干净”的基础文件名 (Base Name)
                # 逻辑：优先从存档的原图路径中提取名字，这是最准确的
                clean_name_base = ""
                clean_ext = ""
                
                if "tot_original_path" in img:
                    # 从存档路径提取文件名 (e.g. //Texture/Wood.jpg -> Wood.jpg)
                    orig_path = img["tot_original_path"]
                    # 使用 bpy.path.basename 处理跨平台路径分隔符
                    filename = bpy.path.basename(orig_path)
                    clean_name_base, clean_ext = os.path.splitext(filename)
                else:
                    # 如果没有存档 (极少情况)，尝试从当前文件名反推
                    # 比如当前是 Wood_2048px.jpg，我们需要剥离 _2048px
                    curr_filename = bpy.path.basename(img.filepath)
                    name_temp, clean_ext = os.path.splitext(curr_filename)
                    # 使用正则去掉结尾的 _数字px
                    clean_name_base = re.sub(r'_\d+px$', '', name_temp)

                if not clean_name_base:
                    continue

                # 2. 构造目标文件夹路径 (e.g. C:\Project\textures_1024px)
                folder_name = f"textures_{target}px"
                
                # 判断是使用自定义路径还是默认路径
                # 这里为了简单，我们扫描默认路径。如果你开启了自定义路径，逻辑需对应调整。
                # 通常建议切换功能主要在默认路径下工作，或者存储输出路径到属性里。
                # 这里假设是在 blend 同级目录下：
                target_dir_abs = os.path.join(base_path, folder_name)
                
                # 3. 构造目标文件名 (e.g. Wood_1024px.jpg)
                target_filename = f"{clean_name_base}_{target}px{clean_ext}"
                target_fullpath_abs = os.path.join(target_dir_abs, target_filename)

                # 4. 核心检查：文件真的存在吗？
                if os.path.exists(target_fullpath_abs):
                    # 构造相对路径赋值给 Blender (//textures_1024px/...) 以便携带
                    rel_path = f"//{folder_name}/{target_filename}"
                    img.filepath = rel_path
                    img.reload()
                    switched_count += 1
                else:
                    # 调试信息：如果切换失败，控制台会打印它想找什么但没找到
                    # print(f"[TOT] Target not found: {target_fullpath_abs}")
                    pass
        
        # 刷新列表 UI
        bpy.ops.tot.updateimagelist()
        
        msg = f"Restored {switched_count} images to Original." if target == 'ORIGINAL' else f"Switched {switched_count} images to {target}px."
        self.report({'INFO'}, msg)
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