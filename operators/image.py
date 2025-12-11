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
                # ... (前面获取 clean_name_base 的逻辑不变) ...

                # 构造目标文件夹路径
                # [修改点]：如果 target 是 "camera_optimized"，不做 px 拼接
                if target == "camera_optimized":
                    folder_name = "textures_camera_optimized"
                else:
                    folder_name = f"textures_{target}px"
                
                target_dir_abs = os.path.join(base_path, folder_name)
                
                # 因为 optimized 文件夹里，Wood 可能是 Wood_512px.jpg，也可能是 Wood_2048px.jpg
                # 我们不能简单拼写文件名，我们需要去文件夹里“找”对应的前缀文件
                
                found_file = None
                
                if os.path.exists(target_dir_abs):
                    # 遍历该文件夹下的所有文件，寻找匹配 clean_name_base 的文件
                    # 比如 clean_name_base 是 "Wood"，我们要找 "Wood_xxxpx.jpg"
                    for f in os.listdir(target_dir_abs):
                        if f.startswith(clean_name_base):
                            # 简单的匹配：文件名包含 base name
                            # 严谨一点：f 必须是 Base + "_" + 数字 + "px" + ext
                            if clean_name_base in f:
                                found_file = f
                                break 
                
                if found_file:
                    target_fullpath_abs = os.path.join(target_dir_abs, found_file)
                    
                    rel_path = f"//{folder_name}/{found_file}"
                    img.filepath = rel_path
                    img.reload()
                    switched_count += 1
                else:
                    # 没找到对应文件（可能是因为该图片在优化时被判断为不可见，所以没生成）
                    pass
        
        # 刷新列表 UI
        bpy.ops.tot.updateimagelist()
        
        msg = f"Restored {switched_count} images to Original." if target == 'ORIGINAL' else f"Switched {switched_count} images to {target}px."
        self.report({'INFO'}, msg)
        return {'FINISHED'}
    
class TOT_OT_OptimizeByCamera(bpy.types.Operator):
    """根据相机视角自动计算并生成优化贴图"""
    bl_idname = "tot.optimize_by_camera"
    bl_label = "Optimize by Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        cam = scn.lod_camera or context.scene.camera
        
        if not cam:
            self.report({'ERROR'}, "No active camera found!")
            return {'CANCELLED'}

        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}

        # 1. 准备输出目录
        folder_name = "textures_camera_optimized"
        output_dir = os.path.join(base_path, folder_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. 建立 [图片 -> 最大所需像素] 的映射表
        # 默认给一个极小值 (比如 32px)，如果没有物体用到它，就保持极小或者不处理
        image_res_map = {} 
        
        # 获取场景中所有 Mesh 物体
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and not o.hide_render]
        
        self.report({'INFO'}, f"Analyzing {len(mesh_objs)} objects from Camera view...")
        
        for obj in mesh_objs:
            # A. 计算该物体在屏幕上的像素大小
            px_size, visible = utils.calculate_screen_coverage(context.scene, obj, cam)
            
            if not visible:
                continue # 如果不可见，这个物体对贴图精度无贡献
            
            # 向上取整到最近的 POT (Power of Two: 128, 256, 512...) 
            # 这是一个优化习惯，显卡喜欢 2 的幂次方
            # 简单算法：当前像素 * 质量系数 (比如 1.2 倍以防模糊)
            target_res = px_size * 1.2 
            
            # B. 找到物体引用的所有贴图
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            img = node.image
                            if img.source in {'VIEWER', 'GENERATED'}: continue
                            
                            # C. 记录最大需求
                            # 如果这张图之前被别的物体算过，取最大值
                            current_max = image_res_map.get(img, 0)
                            if target_res > current_max:
                                image_res_map[img] = target_res

        # 3. 开始批量处理图片
        processed_count = 0
        
        # 能够接受的最小/最大尺寸
        MIN_SIZE = 64
        MAX_SIZE = 4096 

        for img, req_px in image_res_map.items():
            # 钳制数值到 POT (简化版，直接钳制数值)
            # 比如算出 900px，我们要存成 1024px
            # 简单的阶梯：
            if req_px <= 64: final_size = 64
            elif req_px <= 128: final_size = 128
            elif req_px <= 256: final_size = 256
            elif req_px <= 512: final_size = 512
            elif req_px <= 1024: final_size = 1024
            elif req_px <= 2048: final_size = 2048
            else: final_size = 4096
            
            # 如果原图本身就很小，不要放大它
            orig_w = img.size[0]
            if final_size > orig_w:
                final_size = orig_w

            # --- 下面是复用之前的 Resize 逻辑 ---
            try:
                # 记录原始路径
                if "tot_original_path" not in img:
                    img["tot_original_path"] = img.filepath

                # 构造文件名：这里不再加 _1024px 后缀，因为每张图后缀不一样会很乱
                # 或者我们可以加后缀，但在 SwitchResolution 时要能够识别
                # 为了保持 Switcher 兼容性，建议保留后缀逻辑，或者统一不加后缀？
                # 方案：加上后缀，方便人类阅读。Switch 逻辑需要微调。
                
                original_filepath = img.filepath_from_user()
                file_name = os.path.basename(original_filepath)
                if not file_name: file_name = f"{img.name}.png"
                name_part, ext_part = os.path.splitext(file_name)
                if not ext_part: ext_part = ".png"

                new_file_name = f"{name_part}_{final_size}px{ext_part}"
                new_full_path = os.path.join(output_dir, new_file_name)

                # 内存缩放 & 保存
                img.scale(final_size, final_size)
                img.save_render(filepath=new_full_path)
                
                # 重连
                img.filepath = new_full_path
                img.reload()
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error optimizing {img.name}: {e}")

        # 4. 刷新列表
        bpy.ops.tot.updateimagelist()
        context.area.tag_redraw()
        
        self.report({'INFO'}, f"Camera Optimized: Generated {processed_count} textures.")
        return {'FINISHED'}

classes = (
    TOT_OT_UpdateImageList,
    TOT_OT_SelectAllImages,
    TOT_OT_ResizeImages,
    TOT_OT_ClearDuplicateImage,
    TOT_OT_DeleteTextureFolder,
    TOT_OT_SwitchResolution,
    TOT_OT_OptimizeByCamera,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)