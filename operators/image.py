import os
import bpy
import shutil
import time
import gc
import subprocess # 替代 threading
import sys        # 用于获取 python 解释器路径
from .. import utils
from ..core.profile import (
    GENERATED_PROFILE_KEY,
    assign_new_uuid,
    ensure_active_profile,
    get_active_profile,
    get_profile_camera,
    get_profile_objects,
)


_active_worker_outputs = {}


def _image_worker_limit():
    available = getattr(os, "process_cpu_count", os.cpu_count)() or os.cpu_count() or 1
    return max(1, available - 2)


def _worker_output_key(path):
    return os.path.normcase(os.path.realpath(path))


def _can_process_image_task(task, worker_limit):
    for process in tuple(_active_worker_outputs):
        if process.poll() is not None:
            del _active_worker_outputs[process]

    if _worker_output_key(task["dst_path"]) in _active_worker_outputs.values():
        return False
    return task["method"] != "PIL" or len(_active_worker_outputs) < worker_limit


def _start_image_worker(worker_script, task):
    python_args = [arg for arg in getattr(bpy.app, "python_args", ()) if arg != "-I"]
    cmd = [sys.executable] + python_args + [worker_script,
        "--src", task["src_path"],
        "--dst", task["dst_path"],
        "--size", str(task["target_size"]),
        "--action", task["action"],
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(os.path.abspath(path) for path in sys.path)
    output_key = _worker_output_key(task["dst_path"])
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    _active_worker_outputs[process] = output_key
    return process


# 延迟导入pil
def check_pil_available():
    """
    Lazy import check for PIL.
    Only checks when called, avoiding top-level dependency issues.
    """
    try:
        import PIL
        from PIL import Image
        return True
    except ImportError:
        return False

def _is_path_in_directory(path, directory):
    try:
        norm_path = os.path.normcase(os.path.realpath(path))
        norm_dir = os.path.normcase(os.path.realpath(directory))
        return os.path.commonpath([norm_path, norm_dir]) == norm_dir
    except (ValueError, OSError):
        return False

def _get_aspect_preserving_size(width, height, target_size):
    if width <= 0 or height <= 0:
        return target_size, target_size

    long_edge = max(width, height)
    if long_edge <= target_size:
        return width, height

    scale = target_size / float(long_edge)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    return new_width, new_height


def _get_original_image_path(image):
    """Return the source path even while a generated variant is active."""
    raw_path = image.get("lod_original_path") or image.filepath
    return bpy.path.abspath(raw_path) if raw_path else ""


def _load_original_image_data(image):
    """Ensure sizing uses the source image, not a previously generated variant."""
    original = image.get("lod_original_path")
    if not original:
        return
    original_abs = bpy.path.abspath(original)
    current_abs = bpy.path.abspath(image.filepath) if image.filepath else ""
    if original_abs and os.path.exists(original_abs) and os.path.normcase(original_abs) != os.path.normcase(current_abs):
        image.filepath = original
        image.reload()
    
class LOD_OT_UpdateImageList(bpy.types.Operator):
    bl_idname = "lod.updateimagelist"
    bl_label = "Update Image List"


    def execute(self, context):
        scn = context.scene.lod_props
        ensure_active_profile(context.scene)
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
                "packed_status": 0,
                "dimensions": f"{img.size[0]} x {img.size[1]}" if img.size[0] > 0 else "Unknown"
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
            item.image_dimensions = data["dimensions"]
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
    """Use subprocess to call an external worker.py script for image processing."""
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
    TIME_BUDGET = 0.02      # 主线程每帧处理 Native 任务的时间

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        if event.type == 'TIMER':
            
            # --- A. 检查正在运行的子进程 ---
            # 倒序遍历以便安全移除
            for i in range(len(self._active_processes) - 1, -1, -1):
                proc, task_data = self._active_processes[i]
                
                # 检查进程是否结束
                ret_code = proc.poll()
                
                if ret_code is not None:
                    # 进程已结束，获取输出
                    try:
                        stdout_data, stderr_data = proc.communicate(timeout=0.2)
                    except:
                        stdout_data, stderr_data = "", ""
                    
                    if ret_code == 0 and "SUCCESS" in stdout_data:
                        # 成功：在主线程刷新图片
                        self.handle_worker_success(task_data)
                        self._processed += 1
                    else:
                        # 失败：打印错误
                        img_name = task_data["img_name"]
                        print(f"[LODify] Worker Failed for {img_name} (Code {ret_code}). Fallback to Native.")
                        if stderr_data: print(f"  Debug: {stderr_data}")
                        # 但为了代码简单，这里只做报错
                        # 将任务模式改为 "NATIVE" 并放回队列头部
                        task_data["method"] = "NATIVE"
                        self._task_queue.insert(0, task_data)
                        ## 统计数不增加，只移除失败的进程

                    # 从活动列表中移除
                    _active_worker_outputs.pop(proc, None)
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
                if not _can_process_image_task(self._task_queue[0], self._worker_limit):
                    break
                task = self._task_queue.pop(0)
                if task["method"] == "PIL":
                    self.spawn_worker_process(task)
                else:
                    # 原生任务必须在主线程执行
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
        ensure_active_profile(context.scene)
        
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Please save the .blend file first!")
            return {'CANCELLED'}

        # --- 1. 定位 worker.py 路径 ---
        # 假设当前文件在 addons/LODify/operators/image.py
        # worker.py 在 addons/LODify/worker.py
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../operators
        root_dir = os.path.dirname(current_dir)                  # .../LODify
        self._worker_script = os.path.join(root_dir, "core", "image_worker.py")
        
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
            _load_original_image_data(img)
            
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
            elif check_pil_available():
                if not img.packed_file and img.filepath:
                     abs_path = _get_original_image_path(img)
                     if os.path.exists(abs_path):
                         method = "PIL"
            
            # 记录原始路径
            if "lod_original_path" not in img:
                img["lod_original_path"] = img.filepath

            # 构造文件名
            original_filepath = img.get("lod_original_path") or img.filepath_from_user()
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
                "src_path": _get_original_image_path(img),
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
        self._worker_limit = _image_worker_limit()
        
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        pil_count = sum(1 for t in self._task_queue if t["method"] == "PIL")
        self.report({'INFO'}, f"Starting: {pil_count} worker tasks, {self._total_tasks - pil_count} Blender tasks. Worker limit: {self._worker_limit}.")
        return {'RUNNING_MODAL'}

    def spawn_worker_process(self, task):
        try:
            process = _start_image_worker(self._worker_script, task)
            self._active_processes.append((process, task))
        except Exception as error:
            print(f"Failed to spawn worker: {error}")
            task["method"] = "NATIVE"
            self._task_queue.insert(0, task)

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
            new_width, new_height = _get_aspect_preserving_size(img.size[0], img.size[1], target_size)
            img.scale(new_width, new_height)
            
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

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        for proc, _task in self._active_processes:
            if proc.poll() is None:
                proc.terminate()
        self._active_processes.clear()
        context.window_manager.progress_end()
        self.report({'WARNING'}, "Image resize cancelled; generated files were kept.")
    
class LOD_OT_ClearDuplicateImage(bpy.types.Operator):
    bl_idname = "lod.clearduplicateimage"
    bl_label = "Clear Duplicate Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ensure_active_profile(context.scene)
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

        profile = ensure_active_profile(context.scene)
        for obj in get_profile_objects(context.scene, profile):
            if obj.type != 'MESH':
                continue
            for slot_index, slot in enumerate(obj.material_slots):
                material = slot.material
                if not material or not material.use_nodes or not material.node_tree:
                    continue
                duplicate_nodes = [
                    node for node in material.node_tree.nodes
                    if node.type == 'TEX_IMAGE' and node.image and node.image.name in remap_dict
                ]
                if not duplicate_nodes:
                    continue
                if material.get(GENERATED_PROFILE_KEY) != profile.profile_id:
                    variant = material.copy()
                    assign_new_uuid(variant)
                    variant.name = f"LODify_{profile.profile_id[:8]}_{obj.name}_{slot_index}"
                    variant[GENERATED_PROFILE_KEY] = profile.profile_id
                    slot.material = variant
                    material = variant
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image and node.image.name in remap_dict:
                        node.image = remap_dict[node.image.name]
                        cleaned_count += 1
        
        # Keep both source images and duplicate datablocks. A profile restore
        # must never depend on Blender's global orphan purge.
        
        bpy.ops.lod.updateimagelist()
        self.report({'INFO'}, f"Replaced {cleaned_count} duplicate image references.")
        return {'FINISHED'}

class LOD_OT_DeleteTextureFolder(bpy.types.Operator):
    bl_idname = "lod.delete_texture_folder"
    bl_label = "Delete Folder"
    bl_options = {'REGISTER', 'UNDO'} 
    folder_name: bpy.props.StringProperty() 

    def execute(self, context):
        ensure_active_profile(context.scene)
        base_path = bpy.path.abspath("//")
        if not base_path: return {'CANCELLED'}
        
        target_path_abs = os.path.join(base_path, self.folder_name)
        target_path_abs = os.path.normpath(target_path_abs) # 标准化路径

        if (
            not self.folder_name.startswith("textures_")
            or not _is_path_in_directory(target_path_abs, base_path)
            or os.path.normcase(target_path_abs) == os.path.normcase(os.path.normpath(base_path))
        ):
            self.report({'ERROR'}, "Only generated texture folders inside the Blend directory can be deleted.")
            return {'CANCELLED'}
        
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
                if _is_path_in_directory(img_abs, target_path_abs):
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
        ensure_active_profile(context.scene)
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
    TIME_BUDGET = 0.02    

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
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
                            # 失败处理：直接在当前帧转 Native 执行
                            print(f"[LOD] CamOpt Worker Failed (Code {ret_code}). Debug: {stderr_data}")
                            print("Switched to Native fallback.")
                            # 强制修改方法并立即执行
                            task_data["method"] = "NATIVE"

                            try:
                                self.process_native_fallback(task_data)
                            except Exception as e:
                                print(f"Native Fallback Error: {e}")    
                               
                        self._processed += 1
                        _active_worker_outputs.pop(proc, None)
                        self._active_processes.pop(i)
                
                # B. 检查完成
                if not self._queue and not self._active_processes:
                    self._phase = 'FINISHED'
                
                # C. 分发新任务
                start_time = time.time()
                while self._queue:
                    if (time.time() - start_time) > self.TIME_BUDGET:
                        break
                    
                    # 取出任务 (img object, pixel_int)
                    img, req_px = self._queue[0]
                    task_data = self.prepare_task_data(img, req_px)
                    if not _can_process_image_task(task_data, self._worker_limit):
                        break
                    
                    # 移除队列头
                    self._queue.pop(0)

                    if os.path.exists(task_data["dst_path"]):
                        img.filepath = task_data["dst_path"]
                        img.reload()
                        self._processed += 1 
                        continue
                        
                    if task_data["method"] == "PIL":
                        self.spawn_worker_process(task_data)
                    else:
                        # Native 任务直接跑
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
        profile = ensure_active_profile(context.scene)
        cam = get_profile_camera(context.scene, profile)
        
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
        self._worker_script = os.path.join(root_dir, "core", "image_worker.py")

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        
        self._phase = 'ANALYZING'
        self._queue = []
        self._processed = 0
        self._worker_limit = _image_worker_limit()
        self._output_dir = os.path.join(base_path, "textures_camera_optimized")
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir, exist_ok=True)
            
        self.report({'INFO'}, f"Starting Camera Optimization. Worker limit: {self._worker_limit}.")
        return {'RUNNING_MODAL'}

    def spawn_worker_process(self, task):
        try:
            process = _start_image_worker(self._worker_script, task)
            self._active_processes.append((process, task))
        except Exception as error:
            print(f"Failed to spawn worker: {error}")
            try:
                self.process_native_fallback(task)
            except Exception as fallback_error:
                print(f"Native Fallback Error: {fallback_error}")
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
        profile = ensure_active_profile(context.scene)
        cam = get_profile_camera(context.scene, profile)

        if scn.resize_size == 'c':
            user_max_cap = scn.custom_resize_size
        else:
            try: user_max_cap = int(scn.resize_size)
            except: user_max_cap = 4096

        ABSOLUTE_MIN_FLOOR = 32
        image_res_map = {}
        instance_sources = utils.get_instance_sources(context.scene)
        mesh_objs = [o for o in get_profile_objects(context.scene, profile) if o.type == 'MESH' and not o.hide_render]

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
        _load_original_image_data(img)
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

        original_filepath = img.get("lod_original_path") or img.filepath_from_user()
        file_name = os.path.basename(original_filepath)
        if not file_name: file_name = f"{img.name}.png"
        name_part, ext_part = os.path.splitext(file_name)
        if not ext_part: ext_part = ".png"

        new_file_name = f"{name_part}_{final_size}px{ext_part}"
        new_full_path = os.path.join(self._output_dir, new_file_name)

        method = "NATIVE"
        action = "RESIZE"

        ext = ext_part.lower()
        if img.filepath:
            ext = os.path.splitext(img.filepath)[1].lower()

        if ext in {'.exr', '.hdr'}:
            method = "PIL"
            action = "COPY"
        elif check_pil_available():
            if not img.packed_file and img.filepath:
                 abs_path = _get_original_image_path(img)
                 if os.path.exists(abs_path):
                     method = "PIL"
        
        task_data = {
            "img_name": img.name,
            "target_size": final_size,
            "src_path": _get_original_image_path(img),
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
            new_width, new_height = _get_aspect_preserving_size(img.size[0], img.size[1], target_size)
            img.scale(new_width, new_height)
            
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
        for area in context.screen.areas: area.tag_redraw()
            
        self.report({'INFO'}, f"Camera Optimization Complete! Processed {self._processed} textures.")


    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        for proc, _task in self._active_processes:
            if proc.poll() is None:
                proc.terminate()
        self._active_processes.clear()
        context.window_manager.progress_end()
        self.report({'WARNING'}, "Camera optimization cancelled; generated files were kept.")


class LOD_OT_CleanUnusedMaterialSlots(bpy.types.Operator):
    """Remove material slots that are not used by any face/spline"""
    bl_idname = "lod.clean_unused_material_slots"
    bl_label = "Clean Unused Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        profile = ensure_active_profile(context.scene)
        total_removed = 0
        objects_cleaned = 0
        
        # 遍历所有物体
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data and obj.data.get(GENERATED_PROFILE_KEY) != profile.profile_id:
                # The profile snapshot stores the source mesh; edit a private copy.
                try:
                    mesh_copy = obj.data.copy()
                    assign_new_uuid(mesh_copy)
                    mesh_copy.name = f"LODify_Cleanup_{obj.name}"
                    mesh_copy[GENERATED_PROFILE_KEY] = profile.profile_id
                    obj.data = mesh_copy
                except Exception:
                    pass
            removed = self.clean_object_slots(obj)
            if removed > 0:
                total_removed += removed
                objects_cleaned += 1
        
        if total_removed > 0:
            self.report({'INFO'}, f"Cleaned {total_removed} unused slots from {objects_cleaned} objects.")
        else:
            self.report({'INFO'}, "No unused material slots found.")
        
        return {'FINISHED'}
    
    def clean_object_slots(self, obj):
        """清理单个物体的未使用材质插槽，返回删除的数量"""
        
        # 检查物体是否有材质插槽
        if not obj.material_slots:
            return 0
        
        # 根据物体类型获取已使用的材质索引
        used_indices = set()
        
        if obj.type == 'MESH':
            # MESH: 检查多边形的 material_index
            mesh = obj.data
            if mesh and hasattr(mesh, 'polygons'):
                for poly in mesh.polygons:
                    used_indices.add(poly.material_index)
                    
        elif obj.type == 'CURVE':
            # CURVE: 检查每个样条的 material_index
            curve = obj.data
            if curve and hasattr(curve, 'splines'):
                for spline in curve.splines:
                    used_indices.add(spline.material_index)
                    
        elif obj.type == 'SURFACE':
            # SURFACE: 同样检查样条
            surface = obj.data
            if surface and hasattr(surface, 'splines'):
                for spline in surface.splines:
                    used_indices.add(spline.material_index)
                    
        elif obj.type == 'META':
            # META: 元球通常只使用一个材质 (索引 0)
            # 保守处理：只保留索引 0
            if len(obj.material_slots) > 0:
                used_indices.add(0)
                
        elif obj.type == 'FONT':
            # FONT: 文本物体通常只使用一个材质
            # 保守处理：只保留索引 0
            if len(obj.material_slots) > 0:
                used_indices.add(0)
                
        elif obj.type == 'GPENCIL':
            # GREASE PENCIL: 检查所有图层和笔画
            gpd = obj.data
            if gpd:
                for layer in gpd.layers:
                    for frame in layer.frames:
                        for stroke in frame.strokes:
                            used_indices.add(stroke.material_index)
        else:
            # 其他类型不处理
            return 0
        
        # 如果没有检测到任何使用的索引，且物体有材质插槽
        # 保守起见，保留第一个插槽
        if not used_indices and len(obj.material_slots) > 0:
            used_indices.add(0)
        
        # 从后向前删除未使用的插槽 (避免索引变化问题)
        removed_count = 0
        slot_count = len(obj.material_slots)
        
        for i in range(slot_count - 1, -1, -1):
            if i not in used_indices:
                # 设置活动材质索引并删除
                obj.active_material_index = i
                
                # 使用 override 来确保操作在正确的上下文中执行
                with bpy.context.temp_override(object=obj):
                    try:
                        bpy.ops.object.material_slot_remove()
                        removed_count += 1
                    except Exception as e:
                        print(f"[LOD] Failed to remove slot {i} from {obj.name}: {e}")
        
        return removed_count


classes = (
    LOD_OT_UpdateImageList,
    LOD_OT_SelectAllImages,
    LOD_OT_ResizeImagesAsync,
    LOD_OT_ClearDuplicateImage,
    LOD_OT_CleanUnusedMaterialSlots,
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
