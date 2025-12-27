# File Path: .\operators\image.py

import os
import bpy
import shutil
import time
import gc
import subprocess # 替代 threading
import sys        # 用于获取 python 解释器路径
from .. import utils

# 仍然保留这个检查，仅用于 UI 提示用户是否安装了 PIL
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class LOD_OT_UpdateImageList(bpy.types.Operator):
    bl_idname = "lod.updateimagelist"
    bl_label = "Update Image List"
    
    def execute(self, context):
        scn = context.scene.lod_props
        scn.image_list.clear()
        
        total_size_mb = 0.0
        count = 0
        
        temp_data_list = []

        for img in bpy.data.images:
            if img.name in {'Render Result', 'Viewer Node'}: continue
            if img.source == 'GENERATED': continue

            is_world_tex = False
            if bpy.context.scene.world and bpy.context.scene.world.node_tree:
                for n in bpy.context.scene.world.node_tree.nodes:
                    if n.type == 'TEX_ENVIRONMENT' and n.image == img:
                        is_world_tex = True
                        break
            if is_world_tex: continue

            # 提前计算大小
            size_str = utils.get_image_size_str(img)
            try:
                size_float = float(size_str)
            except:
                size_float = 0.0
            
            total_size_mb += size_float
            count += 1
            
            # 将数据存入临时字典
            img_data = {
                "obj": img,
                "size_str": size_str,
                "size_float": size_float,
                "packed_status": 0
            }
            
            # 预先判断打包状态
            if img.packed_file:
                img_data["packed_status"] = 1 # Packed
            elif img.library:
                img_data["packed_status"] = 2 # Linked
            else:
                img_data["packed_status"] = 0 # File
                
            temp_data_list.append(img_data)
            
        # 按 size_float 降序排序
        temp_data_list.sort(key=lambda x: x["size_float"], reverse=True)

        # 填入 UI 列表
        for data in temp_data_list:
            item = scn.image_list.add()
            item.lod_image_name = data["obj"].name
            item.image_size = data["size_str"]
            item.packed_img = data["packed_status"]
            item.image_selected = False 
            
        scn.r_total_images = count
        scn.total_image_memory = f"{total_size_mb:.2f}"
        
        return {'FINISHED'}

class LOD_OT_SelectAllImages(bpy.types.Operator):
    bl_idname = "lod.imglistselectall"
    bl_label = "Select All"
    
    def execute(self, context):
        scn = context.scene.lod_props
        has_unselected = any(not i.image_selected for i in scn.image_list)
        for i in scn.image_list:
            i.image_selected = has_unselected
        return {'FINISHED'}


# =============================================================================
#  核心修改：基于 Subprocess 的异步缩放 Operator
# =============================================================================

class LOD_OT_ResizeImagesAsync(bpy.types.Operator):
    """
    修改说明：
    使用 subprocess 替代 threading。调用外部 worker.py 脚本处理图片。
    更稳定，符合 Blender 插件审核规范。
    """
    bl_idname = "lod.resizeimages_async"
    bl_label = "Resize Images (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _task_queue = []        # 待处理任务 (字典列表)
    _active_processes = []  # 正在运行的子进程列表: [(process_obj, task_data), ...]
    
    _processed = 0
    _total_tasks = 0
    _worker_script = ""     # worker.py 的路径
    
    # 并发配置
    MAX_PROCESSES = 4       # 同时运行的子进程数量
    TIME_BUDGET = 0.02      # 主线程每帧处理 Native 任务的时间

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            # --- A. 检查正在运行的子进程 ---
            # 倒序遍历以便安全移除
            for i in range(len(self._active_processes) - 1, -1, -1):
                proc, task_data = self._active_processes[i]
                
                # 检查进程是否结束
                ret_code = proc.poll()
                
                if ret_code is not None:
                    # 进程已结束，获取输出
                    # communicate 会阻塞，但因为 poll 已经确认结束，所以这里会瞬间完成
                    stdout_data, stderr_data = proc.communicate()
                    
                    if ret_code == 0 and "SUCCESS" in stdout_data:
                        # 成功：在主线程刷新图片
                        self.handle_worker_success(task_data)
                    else:
                        # 失败：打印错误
                        img_name = task_data["img_name"]
                        err_msg = stderr_data if stderr_data else stdout_data
                        print(f"[LODify] Worker Failed for {img_name}: {err_msg}")
                        # 可选：如果是因为没装 PIL 导致的失败，可以考虑在这里触发回退逻辑
                        # 但为了代码简单，这里只做报错
                    
                    self._processed += 1
                    # 从活动列表中移除
                    self._active_processes.pop(i)

            # --- B. 调度新任务 ---
            if not self._task_queue and not self._active_processes:
                return self.finish(context)
            
            start_time = time.time()
            
            while self._task_queue:
                # 1. 检查 Native 时间预算
                if (time.time() - start_time) > self.TIME_BUDGET:
                    break
                
                # 2. 预读任务
                next_task = self._task_queue[0]
                
                if next_task["method"] == "PIL":
                    # 检查进程池是否已满
                    if len(self._active_processes) < self.MAX_PROCESSES:
                        task = self._task_queue.pop(0)
                        self.spawn_worker_process(task)
                    else:
                        # 进程池满了，等待下一帧
                        break
                        
                elif next_task["method"] == "NATIVE":
                    # 原生任务必须在主线程执行
                    task = self._task_queue.pop(0)
                    try:
                        self.process_native_image(task)
                    except Exception as e:
                        print(f"Native Error: {e}")
                    self._processed += 1

            # 更新进度条
            context.window_manager.progress_update(self._processed)
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.lod_props
        
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Please save the .blend file first!")
            return {'CANCELLED'}

        # --- 1. 定位 worker.py 路径 ---
        # 假设当前文件在 addons/LODify/operators/image.py
        # worker.py 在 addons/LODify/worker.py
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../operators
        root_dir = os.path.dirname(current_dir)                  # .../LODify
        self._worker_script = os.path.join(root_dir, "worker.py")
        
        if not os.path.exists(self._worker_script):
            self.report({'ERROR'}, f"Worker script not found at: {self._worker_script}")
            return {'CANCELLED'}

        # 准备输出目录
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
            os.makedirs(self.output_dir, exist_ok=True)

        # 构建任务队列
        self._task_queue = []
        self._active_processes = []
        
        for item in scn.image_list:
            if not item.image_selected: continue
            
            img = bpy.data.images.get(item.lod_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue
            
            # --- 智能分流策略 ---
            method = "NATIVE"
            action = "RESIZE"
            
            ext = ""
            if img.filepath:
                ext = os.path.splitext(img.filepath)[1].lower()

            # HDR/EXR 保护
            if ext in {'.exr', '.hdr'}:
                print(f"[LOD] Copying HDR/EXR (No Resize): {img.name}")
                method = "PIL" # 使用子进程进行文件拷贝，避免主线程 IO 卡顿
                action = "COPY"
            
            # 只有当安装了 PIL 且文件在本地时，才使用子进程
            elif HAS_PIL:
                if not img.packed_file and img.filepath:
                     abs_path = bpy.path.abspath(img.filepath)
                     if os.path.exists(abs_path):
                         method = "PIL"
            
            # 记录原始路径
            if "lod_original_path" not in img:
                img["lod_original_path"] = img.filepath

            # 构造文件名
            original_filepath = img.filepath_from_user()
            file_name = os.path.basename(original_filepath)
            if not file_name: file_name = f"{img.name}.png"
            name_part, ext_part = os.path.splitext(file_name)
            if not ext_part: ext_part = ".png"
            
            if action == "COPY":
                final_ext = ext 
            else:
                final_ext = ext_part
            
            new_file_name = f"{name_part}_{self.target_size}px{ext_part}"
            new_full_path = os.path.join(self.output_dir, new_file_name)

            task_data = {
                "img_name": item.lod_image_name,
                "target_size": self.target_size,
                "src_path": bpy.path.abspath(img.filepath), 
                "dst_path": new_full_path,                 
                "method": method,
                "action": action
            }
            self._task_queue.append(task_data)

        if not self._task_queue:
            self.report({'WARNING'}, "No images selected.")
            return {'CANCELLED'}

        self._total_tasks = len(self._task_queue)
        self._processed = 0
        
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        pil_count = sum(1 for t in self._task_queue if t["method"] == "PIL")
        self.report({'INFO'}, f"Starting: {pil_count} via Worker (Fast), {self._total_tasks - pil_count} via Blender (Slow).")
        return {'RUNNING_MODAL'}

    def spawn_worker_process(self, task):
        """启动一个子进程来执行任务"""
        # 构建命令： python worker.py --src ... --dst ...
        cmd = [
            sys.executable,  # 使用 Blender 自带的 Python
            self._worker_script,
            "--src", task["src_path"],
            "--dst", task["dst_path"],
            "--size", str(task["target_size"]),
            "--action", task["action"]
        ]
        
        try:
            # 启动子进程，接管 stdout 和 stderr
            # text=True 确保返回字符串而不是字节
            # creationflags=subprocess.CREATE_NO_WINDOW (可选，防止 Windows 弹窗，但在 Blender 内部通常不需要)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8' # 强制编码
            )
            self._active_processes.append((proc, task))
            
        except Exception as e:
            print(f"Failed to spawn worker: {e}")
            # 如果启动失败，尝试降级到 Native 处理（或者标记失败）
            # 这里简单处理为标记完成
            self._processed += 1

    def handle_worker_success(self, task):
        """子进程成功后的回调"""
        img = bpy.data.images.get(task["img_name"])
        if not img: return
        
        try:
            # 热重载
            if hasattr(img, "filepath"):
                rel_path = bpy.path.relpath(task["dst_path"])
                img.filepath = rel_path
            img.reload()
        except Exception as e:
            print(f"Reload Error: {e}")

    def process_native_image(self, task):
        """Native Fallback (保持原有逻辑)"""
        img = bpy.data.images.get(task["img_name"])
        if not img: return
        
        target_size = task["target_size"]
        new_full_path = task["dst_path"]
        
        if img.size[0] > target_size or img.size[1] > target_size:
            img.scale(target_size, target_size)
            
        render = bpy.context.scene.render.image_settings
        old_fmt = render.file_format
        old_mode = render.color_mode
        
        try:
            ext = os.path.splitext(new_full_path)[1].lower()
            if ext in {'.jpg', '.jpeg'}:
                render.file_format = 'JPEG'
                render.color_mode = 'RGB'
            elif ext == '.png':
                render.file_format = 'PNG'
                render.color_mode = 'RGBA'
                
            img.save_render(filepath=new_full_path)
        finally:
            render.file_format = old_fmt
            render.color_mode = old_mode
            
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        bpy.ops.lod.updateimagelist()
        gc.collect() 
        
        self.report({'INFO'}, f"Resize Complete! {self._processed} images processed.")
        return {'FINISHED'}
    
class LOD_OT_ClearDuplicateImage(bpy.types.Operator):
    bl_idname = "lod.clearduplicateimage"
    bl_label = "Clear Duplicate Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cleaned_count = 0
        remap_dict = {} 
        
        all_images = list(bpy.data.images)
        for img in all_images:
            if len(img.name) > 4 and img.name[-4] == '.' and img.name[-3:].isdigit():
                base_name = img.name[:-4] 
                original_img = bpy.data.images.get(base_name)
                
                if original_img and original_img != img:
                    try:
                        path1 = os.path.normpath(bpy.path.abspath(img.filepath))
                        path2 = os.path.normpath(bpy.path.abspath(original_img.filepath))
                        if path1 != path2:
                            continue
                    except Exception:
                        continue
                    
                    remap_dict[img.name] = original_img

        if not remap_dict:
            self.report({'INFO'}, "No duplicate images found.")
            return {'FINISHED'}

        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree: continue
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    if node.image.name in remap_dict:
                        target_img = remap_dict[node.image.name]
                        node.image = target_img
                        cleaned_count += 1
        
        # Purge logic
        for img in list(bpy.data.images):
            if img.users == 0:
                if len(img.name) > 4 and img.name[-3:].isdigit():
                    bpy.data.images.remove(img)
        
        bpy.ops.lod.updateimagelist()
        self.report({'INFO'}, f"Replaced {cleaned_count} duplicate image references.")
        return {'FINISHED'}

class LOD_OT_DeleteTextureFolder(bpy.types.Operator):
    bl_idname = "lod.delete_texture_folder"
    bl_label = "Delete Folder"
    bl_options = {'REGISTER', 'UNDO'} 
    folder_name: bpy.props.StringProperty() 

    def execute(self, context):
        base_path = bpy.path.abspath("//")
        if not base_path: return {'CANCELLED'}
        
        target_path_abs = os.path.join(base_path, self.folder_name)
        target_path_abs = os.path.normpath(target_path_abs) # 标准化路径
        
        if os.path.exists(target_path_abs):
            # 检查是否有图片正在使用这个文件夹里的文件，如果有，强制切回原图
            restored_count = 0
            for img in bpy.data.images:
                if img.source in {'VIEWER', 'GENERATED'}: continue
                if not img.filepath: continue
                
                # 获取该图片的绝对路径
                try:
                    img_abs = os.path.normpath(bpy.path.abspath(img.filepath))
                except:
                    continue
                
                # 判断：如果图片的路径以 我们要删除的文件夹路径 开头
                # 说明这张图在这个文件夹里
                if img_abs.startswith(target_path_abs):
                    # 尝试恢复原图
                    if "lod_original_path" in img:
                        orig_path = img["lod_original_path"]
                        # 这里我们不做过于严格的 exists 检查，优先保证修改回原本的路径字符串
                        # 哪怕原图丢了，路径指回正确的位置也比指在一个即将删除的文件夹好
                        img.filepath = orig_path
                        try: img.reload()
                        except: pass
                        restored_count += 1
            
            if restored_count > 0:
                print(f"[LOD] Auto-restored {restored_count} images before deleting folder.")

            # - 执行删除 ---
            try:
                shutil.rmtree(target_path_abs)
                
                # 删除后强制刷新列表
                bpy.ops.lod.updateimagelist()
                
                self.report({'INFO'}, f"Deleted folder: {self.folder_name} (Restored {restored_count} images)")
                
                # 强制刷新界面
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
                        
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete: {e}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Folder not found.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
class LOD_OT_SwitchResolution(bpy.types.Operator):
    bl_idname = "lod.switch_resolution"
    bl_label = "Switch Texture Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    target_res: bpy.props.StringProperty()

    def execute(self, context):
        scn = context.scene.lod_props
        target = self.target_res
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}

        switched_count = 0
        fail_count = 0

        for item in scn.image_list:
            img = bpy.data.images.get(item.lod_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue

            # 获取基础文件名用于匹配
            if "lod_original_path" in img:
                raw_filepath = img["lod_original_path"]
            else:
                raw_filepath = img.filepath_from_user()

            file_name = os.path.basename(raw_filepath)
            if not file_name: file_name = img.name
            clean_name_base, _ = os.path.splitext(file_name)

            # --- 切换逻辑 ---
            if target == 'ORIGINAL':
                if "lod_original_path" in img:
                    orig_path = img["lod_original_path"]
                    abs_orig_path = bpy.path.abspath(orig_path)
                    
                    # [优化] 检查原图是否存在
                    if os.path.exists(abs_orig_path):
                        img.filepath = orig_path
                        img.reload()
                        switched_count += 1
                    else:
                        # [兜底策略] 如果原图找不到了，但当前图是坏的（比如被删了），
                        # 那还是强行指回原图路径，至少路径是对的，用户只要把文件放回去就行。
                        # 检查当前图片是否有效 (size 0,0 通常意味着丢失)
                        if img.size[0] == 0:
                            print(f"[LOD] Warning: Original file missing ({abs_orig_path}), but restoring path anyway.")
                            img.filepath = orig_path
                            switched_count += 1
                        else:
                            print(f"[LOD] Skip restore: Original file missing: {abs_orig_path}")
                            fail_count += 1
            else:
                # 切换到其他分辨率 (代码保持不变)
                if target == "camera_optimized":
                    folder_name = "textures_camera_optimized"
                else:
                    folder_name = f"textures_{target}px"

                target_dir_abs = os.path.join(base_path, folder_name)
                found_file = None

                if os.path.exists(target_dir_abs):
                    for f in os.listdir(target_dir_abs):
                        check_prefix = clean_name_base + "_"
                        if f.startswith(check_prefix):
                            found_file = f
                            break
                if found_file:
                    rel_path = f"//{folder_name}/{found_file}"
                    img.filepath = rel_path
                    img.reload()
                    switched_count += 1

        bpy.ops.lod.updateimagelist()
        
        msg = f"Switched {switched_count} images."
        if target == 'ORIGINAL':
            msg = f"Restored {switched_count} images."
            if fail_count > 0:
                msg += f" (Skipped {fail_count} missing originals)"
                
        self.report({'INFO'}, msg)
        return {'FINISHED'}

# =============================================================================
#  Camera Optimization (也改为 Subprocess)
# =============================================================================

class LOD_OT_OptimizeByCamera(bpy.types.Operator):
    bl_idname = "lod.optimize_by_camera"
    bl_label = "Optimize by Camera (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []       # 待处理任务
    _active_processes = [] # 子进程列表
    
    _processed = 0    
    _total_tasks = 0  
    _output_dir = ""  
    _phase = 'INIT'   
    _worker_script = ""

    # 配置
    MAX_PROCESSES = 4     
    TIME_BUDGET = 0.02    

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._phase == 'ANALYZING':
                self.do_analysis(context)
                self._phase = 'PROCESSING'
                self._active_processes = []
                context.window_manager.progress_begin(0, self._total_tasks)
                return {'RUNNING_MODAL'}

            elif self._phase == 'PROCESSING':
                
                # A. 检查活动进程
                for i in range(len(self._active_processes) - 1, -1, -1):
                    proc, task_data = self._active_processes[i]
                    ret_code = proc.poll()
                    if ret_code is not None:
                        stdout_data, stderr_data = proc.communicate()
                        if ret_code == 0 and "SUCCESS" in stdout_data:
                            self.handle_worker_success(task_data)
                        else:
                             print(f"CamOpt Worker Failed: {stderr_data or stdout_data}")
                        self._processed += 1
                        self._active_processes.pop(i)
                
                # B. 检查完成
                if not self._queue and not self._active_processes:
                    self._phase = 'FINISHED'
                
                # C. 分发新任务
                start_time = time.time()
                while self._queue:
                    if (time.time() - start_time) > self.TIME_BUDGET:
                        break
                    
                    # 预读
                    img, req_px = self._queue[0]
                    task_data = self.prepare_task_data(img, req_px)
                    self._queue.pop(0) # 移除

                    if not task_data:
                        self._processed += 1 
                        continue
                        
                    if task_data["method"] == "PIL":
                        if len(self._active_processes) < self.MAX_PROCESSES:
                            self.spawn_worker_process(task_data)
                        else:
                            # 塞回队列头等待下一次
                            self._queue.insert(0, (img, req_px)) 
                            break 
                    else:
                        # Native
                        try:
                            self.process_native_fallback(task_data)
                        except Exception as e:
                            print(f"Native Error: {e}")
                        self._processed += 1

                context.window_manager.progress_update(self._processed)
            
            elif self._phase == 'FINISHED':
                self.finish(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.lod_props
        cam = scn.lod_camera or context.scene.camera
        
        if not cam:
            self.report({'ERROR'}, "No active camera found!")
            return {'CANCELLED'}

        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}
        
        # 查找 worker 路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        self._worker_script = os.path.join(root_dir, "worker.py")

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        
        self._phase = 'ANALYZING'
        self._queue = []
        self._processed = 0
        self._output_dir = os.path.join(base_path, "textures_camera_optimized")
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir, exist_ok=True)
            
        self.report({'INFO'}, "Starting Camera Optimization...")
        return {'RUNNING_MODAL'}

    def spawn_worker_process(self, task):
        cmd = [
            sys.executable, 
            self._worker_script,
            "--src", task["src_path"],
            "--dst", task["dst_path"],
            "--size", str(task["target_size"]),
            "--action", task["action"]
        ]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            self._active_processes.append((proc, task))
        except Exception as e:
            print(f"Failed to spawn worker: {e}")
            self._processed += 1

    def handle_worker_success(self, res):
        """回调"""
        img = bpy.data.images.get(res["img_name"])
        if not img: return
        try:
            if hasattr(img, "filepath") and "dst_path" in res:
                rel_path = bpy.path.relpath(res["dst_path"])
                img.filepath = rel_path
            img.reload()
        except Exception as e:
            print(f"Reload Error: {e}")

    def do_analysis(self, context):
        """分析场景 (逻辑保持不变)"""
        scn = context.scene.lod_props
        cam = scn.lod_camera or context.scene.camera

        if scn.resize_size == 'c':
            user_max_cap = scn.custom_resize_size
        else:
            try: user_max_cap = int(scn.resize_size)
            except: user_max_cap = 4096

        ABSOLUTE_MIN_FLOOR = 32
        image_res_map = {}
        instance_sources = utils.get_instance_sources(context.scene)
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and not o.hide_render]

        for obj in mesh_objs:
            if obj in instance_sources:
                continue
            
            px_size, visible = utils.calculate_screen_coverage(context.scene, obj, cam)
            
            if not visible:
                target_res = 32
            else:
                calculated_res = px_size * 1.2
                target_res = max(calculated_res, ABSOLUTE_MIN_FLOOR)
                target_res = min(target_res, user_max_cap)

            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            img = node.image
                            if img.source in {'VIEWER', 'GENERATED'}: continue
                            current_max = image_res_map.get(img, 0)
                            if target_res > current_max:
                                image_res_map[img] = target_res
        
        for img, req_px in image_res_map.items():
            self._queue.append((img, req_px))
            
        self._total_tasks = len(self._queue)
        print(f"[LOD] Analysis complete. {self._total_tasks} textures to process.")

    def prepare_task_data(self, img, req_px):
        """准备任务数据"""
        final_size = 4
        if req_px <= 4: final_size = 4
        elif req_px <= 8: final_size = 8 
        elif req_px <= 16: final_size = 16
        elif req_px <= 32: final_size = 32
        elif req_px <= 64: final_size = 64
        elif req_px <= 128: final_size = 128
        elif req_px <= 256: final_size = 256
        elif req_px <= 512: final_size = 512
        elif req_px <= 1024: final_size = 1024
        elif req_px <= 2048: final_size = 2048
        else: final_size = 4096
        
        orig_w = img.size[0]
        orig_h = img.size[1]
        max_orig = max(orig_w, orig_h)
        if final_size > max_orig: final_size = max_orig
        if final_size < 4: final_size = 4

        if "lod_original_path" not in img:
            img["lod_original_path"] = img.filepath

        original_filepath = img.filepath_from_user()
        file_name = os.path.basename(original_filepath)
        if not file_name: file_name = f"{img.name}.png"
        name_part, ext_part = os.path.splitext(file_name)
        if not ext_part: ext_part = ".png"

        new_file_name = f"{name_part}_{final_size}px{ext_part}"
        new_full_path = os.path.join(self._output_dir, new_file_name)

        # 缓存检查
        if os.path.exists(new_full_path):
            img.filepath = new_full_path
            img.reload()
            return None 

        method = "NATIVE"
        action = "RESIZE"

        ext = ext_part.lower()
        if img.filepath:
            ext = os.path.splitext(img.filepath)[1].lower()

        if ext in {'.exr', '.hdr'}:
            method = "PIL"
            action = "COPY"
        elif HAS_PIL:
            if not img.packed_file and img.filepath:
                 abs_path = bpy.path.abspath(img.filepath)
                 if os.path.exists(abs_path):
                     method = "PIL"
        
        task_data = {
            "img_name": img.name,
            "target_size": final_size,
            "src_path": bpy.path.abspath(img.filepath), 
            "dst_path": new_full_path,
            "method": method,
            "action": action 
        }
        return task_data

    def process_native_fallback(self, task):
        """原生处理兜底 (保持不变)"""
        img = bpy.data.images.get(task["img_name"])
        if not img: return
        
        target_size = task["target_size"]
        new_full_path = task["dst_path"]
        
        if img.size[0] > target_size or img.size[1] > target_size:
            img.scale(target_size, target_size)
            
        render = bpy.context.scene.render.image_settings
        old_fmt = render.file_format
        old_mode = render.color_mode
        
        try:
            ext = os.path.splitext(new_full_path)[1].lower()
            if ext in {'.jpg', '.jpeg'}:
                render.file_format = 'JPEG'
                render.color_mode = 'RGB'
            elif ext == '.png':
                render.file_format = 'PNG'
                render.color_mode = 'RGBA' 
            img.save_render(filepath=new_full_path)
        finally:
            render.file_format = old_fmt
            render.color_mode = old_mode
            
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        bpy.ops.lod.updateimagelist()

        try:
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except: pass
        
        gc.collect()
        for area in context.screen.areas: area.tag_redraw()
            
        self.report({'INFO'}, f"Camera Optimization Complete! Processed {self._processed} textures.")

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

classes = (
    LOD_OT_UpdateImageList,
    LOD_OT_SelectAllImages,
    LOD_OT_ResizeImagesAsync,
    LOD_OT_ClearDuplicateImage,
    LOD_OT_DeleteTextureFolder,
    LOD_OT_SwitchResolution,
    LOD_OT_OptimizeByCamera,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)