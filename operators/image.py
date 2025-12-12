import os
import re
import bpy
import shutil
from .. import utils 
import time

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

class TOT_OT_ResizeImagesAsync(bpy.types.Operator):
    """异步缩放图片，避免界面卡死"""
    bl_idname = "tot.resizeimages_async"  # 新的 ID
    bl_label = "Resize Images (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []
    _processed = 0
    _total_tasks = 0
    
    # 每一帧允许运行的时间 (秒)，超过则把控制权交还给界面
    TIME_BUDGET = 0.1 

    def modal(self, context, event):
        if event.type == 'TIMER':
            # 如果队列为空，说明处理完毕
            if not self._queue:
                return self.finish(context)
            
            start_time = time.time()
            
            # --- 时间片循环 ---
            while self._queue:
                # 取出一个任务
                task = self._queue.pop(0)
                
                try:
                    self.process_image(task)
                except Exception as e:
                    print(f"Resize Error: {e}")
                
                self._processed += 1
                
                # 检查时间预算：如果处理耗时超过预算，立即暂停，等待下一帧
                if (time.time() - start_time) > self.TIME_BUDGET:
                    break
            
            # 更新进度条
            context.window_manager.progress_update(self._processed)
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.tot_props
        
        # 1. 基础检查
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Please save the .blend file first!")
            return {'CANCELLED'}

        # 2. 准备输出目录 (在开始前只做一次)
        if scn.resize_size == 'c':
            self.target_size = scn.custom_resize_size
        else:
            self.target_size = int(scn.resize_size)

        folder_name = f"textures_{self.target_size}px"
        
        if scn.duplicate_images and not scn.use_same_directory:
            self.output_dir = os.path.join(bpy.path.abspath(scn.custom_output_path), folder_name)
        else:
            self.output_dir = os.path.join(base_path, folder_name)

        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                self.report({'ERROR'}, f"Cannot create directory: {e}")
                return {'CANCELLED'}

        # 3. 构建任务队列
        self._queue = []
        for item in scn.image_list:
            if not item.image_selected: continue
            
            # 验证图片有效性
            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue
            
            # 将任务数据打包存入队列
            self._queue.append({
                "img_name": item.tot_image_name,
                "target_size": self.target_size
            })

        if not self._queue:
            self.report({'WARNING'}, "No images selected.")
            return {'CANCELLED'}

        # 4. 启动模态
        self._total_tasks = len(self._queue)
        self._processed = 0
        
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        self.report({'INFO'}, f"Starting Async Resize: {self._total_tasks} images...")
        return {'RUNNING_MODAL'}

    def process_image(self, task):
        """单个图片处理逻辑 (从原同步代码迁移而来)"""
        img = bpy.data.images.get(task["img_name"])
        target_size = task["target_size"]
        
        if not img: return

        # 0. 记录原始路径
        if "tot_original_path" not in img:
            img["tot_original_path"] = img.filepath

        # 1. 构造文件名
        original_filepath = img.filepath_from_user()
        file_name = os.path.basename(original_filepath)
        if not file_name: file_name = f"{img.name}.png"
        
        name_part, ext_part = os.path.splitext(file_name)
        if not ext_part: ext_part = ".png"
        
        new_file_name = f"{name_part}_{target_size}px{ext_part}"
        new_full_path = os.path.join(self.output_dir, new_file_name)
        
        # 2. 内存缩放
        # 注意：这里我们做个检查，防止重复操作同一个已经是小图的文件
        img.scale(target_size, target_size)
        
        # 3. 物理保存 (这是最耗时的步骤)
        img.save_render(filepath=new_full_path)
        
        # 4. 重连并刷新
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # 刷新列表 UI
        bpy.ops.tot.updateimagelist()
        
        # 强制刷新界面
        for win in context.window_manager.windows:
            for area in win.screen.areas:
                area.tag_redraw()
                
        self.report({'INFO'}, f"Resize Complete! Processed {self._processed} images.")
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
    """【非阻塞版】根据相机视角自动计算并生成优化贴图"""
    bl_idname = "tot.optimize_by_camera"
    bl_label = "Optimize by Camera (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []       # 待处理任务队列
    _processed = 0    # 已处理数量
    _total_tasks = 0  # 总任务数
    _output_dir = ""  # 输出路径
    
    # 状态变量
    _phase = 'INIT'   # INIT -> ANALYZING -> PROCESSING -> FINISHED

    TIME_BUDGET = 0.1

    def modal(self, context, event):
        if event.type == 'TIMER':
            # --- 阶段 1: 分析阶段 ---
            if self._phase == 'ANALYZING':
                self.do_analysis(context)
                self._phase = 'PROCESSING'
                context.window_manager.progress_begin(0, self._total_tasks)
                return {'RUNNING_MODAL'}

            # --- 阶段 2: 动态批处理阶段 ---
            elif self._phase == 'PROCESSING':
                
                # 记录这一帧开始的时间
                start_time = time.time()
                
                # 【核心循环】只要队列不为空，且没超时，就一直干活！
                while self._queue:
                    # 1. 取出任务
                    task_data = self._queue.pop(0)
                    self.process_image_task(task_data)
                    self._processed += 1
                    
                    # 2. 检查时间是否用完
                    # 如果当前操作耗时已经超过了 TIME_BUDGET (比如 0.1秒)
                    # 立即中断循环，把控制权还给 Blender 去刷新 UI
                    if (time.time() - start_time) > self.TIME_BUDGET:
                        break
                
                # 更新进度条 (不管处理了多少张，这一帧结束时更新一次)
                context.window_manager.progress_update(self._processed)
                
                # 如果队列空了，说明做完了
                if not self._queue:
                    self._phase = 'FINISHED'
            
            # --- 阶段 3: 结束 ---
            elif self._phase == 'FINISHED':
                self.finish(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.tot_props
        cam = scn.lod_camera or context.scene.camera
        
        if not cam:
            self.report({'ERROR'}, "No active camera found!")
            return {'CANCELLED'}

        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}

        # 启动定时器，每 0.01 秒触发一次 modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        
        # 初始化状态
        self._phase = 'ANALYZING'
        self._queue = []
        self._processed = 0
        self._output_dir = os.path.join(base_path, "textures_camera_optimized")
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
            
        self.report({'INFO'}, "Starting Camera Optimization...")
        return {'RUNNING_MODAL'}

    def do_analysis(self, context):
        """分析场景，构建任务队列"""
        scn = context.scene.tot_props
        cam = scn.lod_camera or context.scene.camera
        
        # 1. 获取下限
        if scn.resize_size == 'c':
            min_user_floor = scn.custom_resize_size
        else:
            try: min_user_floor = int(scn.resize_size)
            except: min_user_floor = 64
        
        image_res_map = {}
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and not o.hide_render]
        
        # 这一步纯数学计算，通常很快，如果物体数过万才需要拆分
        for obj in mesh_objs:
            px_size, visible = utils.calculate_screen_coverage(context.scene, obj, cam)
            if not visible: continue 
            
            # 基础需求 + 下限保护
            calculated_res = px_size * 1.2 
            target_res = max(calculated_res, min_user_floor)
            
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            img = node.image
                            if img.source in {'VIEWER', 'GENERATED'}: continue
                            current_max = image_res_map.get(img, 0)
                            if target_res > current_max:
                                image_res_map[img] = target_res
        
        # 将 Map 转换为任务列表
        for img, req_px in image_res_map.items():
            self._queue.append((img, req_px))
            
        self._total_tasks = len(self._queue)
        print(f"[TOT] Analysis complete. {self._total_tasks} textures to process.")

    def process_image_task(self, task_data):
        """处理单张图片的逻辑"""
        img, req_px = task_data
        
        # 1. 计算最终尺寸
        final_size = 4
        if req_px <= 4: final_size = 4
        elif req_px <= 8: final_size = 8        
        if req_px <= 16: final_size = 16
        elif req_px <= 32: final_size = 32
        elif req_px <= 64: final_size = 64
        elif req_px <= 128: final_size = 128
        elif req_px <= 256: final_size = 256
        elif req_px <= 512: final_size = 512
        elif req_px <= 1024: final_size = 1024
        elif req_px <= 2048: final_size = 2048
        else: final_size = 4096
        
        # 限制不超过原图
        orig_w = img.size[0]
        orig_h = img.size[1]
        max_orig = max(orig_w, orig_h)
        if final_size > max_orig: final_size = max_orig
        if final_size < 4: final_size = 4

        try:
            # 构造路径
            if "tot_original_path" not in img:
                img["tot_original_path"] = img.filepath

            original_filepath = img.filepath_from_user()
            file_name = os.path.basename(original_filepath)
            if not file_name: file_name = f"{img.name}.png"
            name_part, ext_part = os.path.splitext(file_name)
            if not ext_part: ext_part = ".png"

            new_file_name = f"{name_part}_{final_size}px{ext_part}"
            new_full_path = os.path.join(self._output_dir, new_file_name)

            # --- [关键优化] 智能缓存检查 ---
            # 如果文件已经存在，且我们认为无需覆盖，则直接使用，跳过 scale 和 save
            file_exists = os.path.exists(new_full_path)
            
            if file_exists:
                # 只有当文件存在，我们直接重连，不进行 scale 和 I/O 操作
                # 这会极大地消除“重复运行”时的卡顿
                img.filepath = new_full_path
                img.reload()
                # print(f"Skipped (Cached): {new_file_name}")
            else:
                # 文件不存在，必须生成
                # Scale 和 Save 是最耗时的，这步在 Modal 里执行，不会卡死 UI
                img.scale(final_size, final_size)
                img.save_render(filepath=new_full_path)
                img.filepath = new_full_path
                img.reload()

        except Exception as e:
            print(f"Error processing {img.name}: {e}")

    def finish(self, context):
        """结束清理"""
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        bpy.ops.tot.updateimagelist()
        
        # 强制刷新 UI
        for area in context.screen.areas:
            area.tag_redraw()
            
        self.report({'INFO'}, f"Camera Optimization Complete! Processed {self._processed} textures.")

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

classes = (
    TOT_OT_UpdateImageList,
    TOT_OT_SelectAllImages,
    TOT_OT_ResizeImagesAsync,
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