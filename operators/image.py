import os
import bpy
import shutil
import time
import gc
import threading
import queue
from .. import utils

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[TOT] PIL (Pillow) not found. Falling back to native Blender API.")

class TOT_OT_UpdateImageList(bpy.types.Operator):
    bl_idname = "tot.updateimagelist"
    bl_label = "Update Image List"
    
    def execute(self, context):
        scn = context.scene.tot_props
        scn.image_list.clear()
        
        total_size_mb = 0.0
        count = 0
        
        # --- 1. 创建临时列表用于收集数据 ---
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
            
        # --- 2. 核心修改：按 size_float 降序排序 ---
        # key: 指定排序依据, reverse=True: 降序 (大 -> 小)
        temp_data_list.sort(key=lambda x: x["size_float"], reverse=True)

        # --- 3. 将排序后的数据填入 UI 列表 ---
        for data in temp_data_list:
            item = scn.image_list.add()
            item.tot_image_name = data["obj"].name
            item.image_size = data["size_str"]
            item.packed_img = data["packed_status"]
            # 默认为 False，保持未选中状态
            item.image_selected = False 
            
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

def pil_resize_worker(task_data, result_queue):
    """
    这是一个纯 Python 函数，绝对不要调用任何 bpy.* API
    """
    try:
        src_path = task_data["src_path"]
        dst_path = task_data["dst_path"]
        target_size = task_data["target_size"]
        action = task_data.get("action", "RESIZE") # 获取动作指令

        # [修复逻辑 A]：如果是 HDR/EXR，或者标记为直接复制，则不进行缩放，直接拷贝文件
        if action == "COPY":
            if os.path.normpath(src_path) != os.path.normpath(dst_path):
                shutil.copy2(src_path, dst_path)
            result_queue.put({"status": "COPIED", "img_name": task_data["img_name"], "dst_path": dst_path})
            return

        # 1. 打开图片
        with Image.open(src_path) as img:
            # [修复逻辑 B]：如果是 PNG，打开后立即强制转为 RGBA，防止 resize 过程中丢失 Alpha
            ext = os.path.splitext(dst_path)[1].lower()
            if ext == '.png':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

            # 2. 检查尺寸，防止无效缩放
            width, height = img.size
            if width <= target_size and height <= target_size:
                # 如果不需要缩放，直接复制文件
                if os.path.normpath(src_path) != os.path.normpath(dst_path):
                    shutil.copy2(src_path, dst_path)
                result_queue.put({"status": "COPIED", "img_name": task_data["img_name"], "dst_path": dst_path})
                return

            # 3. 计算新尺寸 (保持比例)
            ratio = min(target_size / width, target_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # 4. 执行缩放
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 5. 保存逻辑
            if ext in ('.jpg', '.jpeg'):
                # JPG 不支持透明，必须转 RGB 并在白底上合成 (或直接转)
                if resized_img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', resized_img.size, (255, 255, 255))
                    # 3.0+ 语法 alpha_composite, 或 paste
                    background.paste(resized_img, mask=resized_img.split()[3]) 
                    resized_img = background
                elif resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                
                resized_img.save(dst_path, quality=95, optimize=True)

            elif ext == '.png':
                # PNG 已经在前面强制转为 RGBA 了，直接保存即可
                resized_img.save(dst_path, optimize=True)
            
            else:
                 resized_img.save(dst_path)
            
        result_queue.put({"status": "SUCCESS", "img_name": task_data["img_name"], "dst_path": dst_path})
         
    except Exception as e:
        result_queue.put({"status": "ERROR", "img_name": task_data["img_name"], "error": str(e)})

class TOT_OT_ResizeImagesAsync(bpy.types.Operator):
    """混合动力缩放：优先使用 PIL 多线程，不支持时回退原生 API"""
    bl_idname = "tot.resizeimages_async"
    bl_label = "Resize Images (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _task_queue = []      # 待处理任务
    _active_threads = []  # 正在运行的线程
    _result_queue = None  # 线程完成后的消息队列
    
    _processed = 0
    _total_tasks = 0
    
    # 线程池配置
    MAX_THREADS = 4       # 同时运行的 PIL 线程数 (防止磁盘 IO 爆炸)
    TIME_BUDGET = 0.02    # 主线程每帧处理原生任务的时间预算

    def modal(self, context, event):
        if event.type == 'TIMER':
            
            # --- A. 处理 PIL 线程的回调结果 ---
            # 只要结果队列里有东西，就在主线程里处理掉 (即执行 bpy 操作)
            while not self._result_queue.empty():
                try:
                    res = self._result_queue.get_nowait()
                    self.handle_pil_result(res)
                    self._processed += 1
                except queue.Empty:
                    break
            
            # --- B. 清理已结束的线程 ---
            # 过滤掉已经执行完的线程
            self._active_threads = [t for t in self._active_threads if t.is_alive()]
            
            # --- C. 调度新任务 ---
            # 如果任务队列空了，且没有活动线程，说明全部搞定
            if not self._task_queue and not self._active_threads:
                return self.finish(context)
            
            # 如果还有任务，且线程池没满，继续分发
            start_time = time.time()
            
            while self._task_queue:
                # 检查是否超时 (针对 Native 任务) 或 线程池满 (针对 PIL 任务)
                if (time.time() - start_time) > self.TIME_BUDGET:
                    break
                    
                # 偷看下一个任务类型，但不取出
                next_task = self._task_queue[0]
                
                if next_task["method"] == "PIL":
                    if len(self._active_threads) < self.MAX_THREADS:
                        # 启动线程
                        task = self._task_queue.pop(0)
                        t = threading.Thread(target=pil_resize_worker, args=(task, self._result_queue))
                        t.daemon = True
                        t.start()
                        self._active_threads.append(t)
                    else:
                        # 线程池满了，这一帧先不发了，等下一帧
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
        scn = context.scene.tot_props
        
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Please save the .blend file first!")
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
        self._result_queue = queue.Queue()
        
        for item in scn.image_list:
            if not item.image_selected: continue
            
            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue
            
            # --- 智能分流策略 ---
            method = "NATIVE"
            action = "RESIZE"
            
            # 获取后缀名
            ext = ""
            if img.filepath:
                ext = os.path.splitext(img.filepath)[1].lower()

            # [修复 2] 绝对禁止 PIL 处理高动态范围图像，防止变紫丢失
            if ext in {'.exr', '.hdr'}:
                print(f"[TOT] Copying HDR/EXR (No Resize): {img.name}")
                # 使用 PIL 线程（因为它其实是文件 IO 线程）来做拷贝，避免卡顿
                method = "PIL" 
                action = "COPY"
            
            # 判据 1: 是否有 PIL 库
            elif HAS_PIL: # 注意这里用了 elif
                # 判据 2: 必须是硬盘上的实体文件 (不能是 Packed/Linked)
                if not img.packed_file and img.filepath:
                     abs_path = bpy.path.abspath(img.filepath)
                     if os.path.exists(abs_path):
                         method = "PIL"
            
            # 记录原始路径 (这对 Hot Swap 很重要)
            if "tot_original_path" not in img:
                img["tot_original_path"] = img.filepath

            # 构造目标文件名
            original_filepath = img.filepath_from_user()
            file_name = os.path.basename(original_filepath)
            if not file_name: file_name = f"{img.name}.png"
            name_part, ext_part = os.path.splitext(file_name)
            if not ext_part: ext_part = ".png"
            
            # [细节] 如果是 COPY 模式，保持原后缀；如果是缩放，通常转 png/jpg
            # 这里为了统一管理，建议 HDR 保持原后缀
            if action == "COPY":
                final_ext = ext # 保持 .exr 或 .hdr
            else:
                final_ext = ext_part
            
            new_file_name = f"{name_part}_{self.target_size}px{ext_part}"
            new_full_path = os.path.join(self.output_dir, new_file_name)

            task_data = {
                "img_name": item.tot_image_name,
                "target_size": self.target_size,
                "src_path": bpy.path.abspath(img.filepath), 
                "dst_path": new_full_path,                 
                "method": method,
                "action": action # 传入动作指令
            }
            self._task_queue.append(task_data)

        if not self._task_queue:
            self.report({'WARNING'}, "No images selected.")
            return {'CANCELLED'}

        self._total_tasks = len(self._task_queue)
        self._processed = 0
        self._active_threads = []
        
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        pil_count = sum(1 for t in self._task_queue if t["method"] == "PIL")
        self.report({'INFO'}, f"Starting: {pil_count} via PIL (Fast), {self._total_tasks - pil_count} via Blender (Slow).")
        return {'RUNNING_MODAL'}

    def handle_pil_result(self, res):
        """PIL 线程完成后，主线程的回调"""
        img = bpy.data.images.get(res["img_name"])
        if not img: return
        
        if res["status"] in {"SUCCESS", "COPIED"}:
            # [核心逻辑] 热重载
            # PIL 已经在后台默默把图改好了，现在告诉 Blender 切换路径并刷新
            # Blender 只需要加载这张小图，完全不经过内存解压大图的过程
            try:
                # 只有当路径真正改变时才设置，避免多余操作
                if hasattr(img, "filepath") and "dst_path" in res:
                    # 使用相对路径更友好
                    rel_path = bpy.path.relpath(res["dst_path"])
                    img.filepath = rel_path
                
                img.reload()
            except Exception as e:
                print(f"Reload Error: {e}")
        else:
            print(f"PIL Failed for {img.name}: {res.get('error')}")

    def process_native_image(self, task):
        """兜底方案：原生 API 处理 (单线程，卡顿，但兼容性好)"""
        img = bpy.data.images.get(task["img_name"])
        if not img: return
        
        # ... (这里保留原有的 Blender Native 处理逻辑，代码结构一致) ...
        # 为了节省篇幅，核心逻辑是 scale() -> save_render() -> reload()
        # 请确保 task["dst_path"] 被正确利用
        
        target_size = task["target_size"]
        new_full_path = task["dst_path"]
        
        # 简单检查尺寸
        if img.size[0] > target_size or img.size[1] > target_size:
            img.scale(target_size, target_size)
            
        # 保存设置备份
        render = bpy.context.scene.render.image_settings
        old_fmt = render.file_format
        old_mode = render.color_mode
        
        try:
            # 根据后缀简单判断格式
            ext = os.path.splitext(new_full_path)[1].lower()
            if ext in {'.jpg', '.jpeg'}:
                render.file_format = 'JPEG'
                render.color_mode = 'RGB'
            elif ext == '.png':
                render.file_format = 'PNG'
                render.color_mode = 'RGBA' # 强制开启透明通道
                
            img.save_render(filepath=new_full_path)
        finally:
            render.file_format = old_fmt
            render.color_mode = old_mode # 还原颜色模式
            
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # 刷新 UI
        bpy.ops.tot.updateimagelist()
        
        # 强力 GC，回收 Native 模式产生的垃圾
        gc.collect() 
        
        self.report({'INFO'}, f"Resize Complete! {self._processed} images processed.")
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
                    # 防止误杀：只有当两个图片指向硬盘上的同一个文件时，才合并！
                    # 获取绝对路径并标准化 (处理 / 和 \ 的差异)
                    try:
                        path1 = os.path.normpath(bpy.path.abspath(img.filepath))
                        path2 = os.path.normpath(bpy.path.abspath(original_img.filepath))

                        # 如果路径不同 (比如一个是 Wood.jpg，一个是 Wood_Normal.jpg 只是名字巧合)，跳过！
                        if path1 != path2:
                            continue

                    except Exception:
                        # 如果路径解析失败（比如是内存生成的图），为了安全起见，跳过
                        continue
                    # 防止误杀：只有当两个图片指向硬盘上的同一个文件时，才合并！
                    # 获取绝对路径并标准化 (处理 / 和 \ 的差异)
                    try:
                        path1 = os.path.normpath(bpy.path.abspath(img.filepath))
                        path2 = os.path.normpath(bpy.path.abspath(original_img.filepath))

                        # 如果路径不同 (比如一个是 Wood.jpg，一个是 Wood_Normal.jpg 只是名字巧合)，跳过！
                        if path1 != path2:
                            continue

                    except Exception:
                        # 如果路径解析失败（比如是内存生成的图），为了安全起见，跳过
                        continue
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
        # 3. 强力清理 (Purge)
        # 这一步是为了让显存/内存立刻释放，而不是等用户重启 Blender
        removed_blocks = 0

        # 遍历所有图片数据块
        # 注意：这里我们遍历的是 list(bpy.data.images)，因为如果在循环中 remove 可能会导致迭代器失效，
        # 所以最好用 list() 包一下或者是小心处理。不过 remove(img) 通常安全。
        for img in bpy.data.images:
            # 只删除 Users 为 0 的图片 (没人用的)
            if img.users == 0:
                # 再次确认一下名字特征，防止误删用户只是暂时没连上的图
                # 逻辑：名字长度 > 4 且 最后3位是数字 (如 .001)
                if len(img.name) > 4 and img.name[-3:].isdigit():
                    bpy.data.images.remove(img)
                    removed_blocks += 1
        # 3. 强力清理 (Purge)
        # 这一步是为了让显存/内存立刻释放，而不是等用户重启 Blender
        removed_blocks = 0

        # 遍历所有图片数据块
        # 注意：这里我们遍历的是 list(bpy.data.images)，因为如果在循环中 remove 可能会导致迭代器失效，
        # 所以最好用 list() 包一下或者是小心处理。不过 remove(img) 通常安全。
        for img in bpy.data.images:
            # 只删除 Users 为 0 的图片 (没人用的)
            if img.users == 0:
                # 再次确认一下名字特征，防止误删用户只是暂时没连上的图
                # 逻辑：名字长度 > 4 且 最后3位是数字 (如 .001)
                if len(img.name) > 4 and img.name[-3:].isdigit():
                    bpy.data.images.remove(img)
                    removed_blocks += 1
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
    target_res: bpy.props.StringProperty()

    def execute(self, context):
        scn = context.scene.tot_props
        target = self.target_res

        # 获取当前 blend 文件的绝对目录

        # 获取当前 blend 文件的绝对目录
        base_path = bpy.path.abspath("//")
        if not base_path:
            self.report({'ERROR'}, "Save file first!")
            return {'CANCELLED'}

        switched_count = 0


        for item in scn.image_list:
            img = bpy.data.images.get(item.tot_image_name)
            if not img: continue
            if img.source in {'VIEWER', 'GENERATED'}: continue

            # ==========================================================
            # [修复点 1]：在此处统一计算 clean_name_base
            # ==========================================================
            # 优先尝试从存档的原始路径获取文件名（最稳妥，防止文件名已经是 _1024px 导致再次叠加）
            if "tot_original_path" in img:
                raw_filepath = img["tot_original_path"]
            else:
                raw_filepath = img.filepath_from_user()

            # 获取文件名 (例如 "Wood.jpg")
            file_name = os.path.basename(raw_filepath)
            if not file_name: file_name = img.name  # 防空回退

            # 去除后缀 (例如 "Wood") -> 这就是 clean_name_base
            clean_name_base, _ = os.path.splitext(file_name)
            # ==========================================================


            # ==========================================================
            # [修复点 1]：在此处统一计算 clean_name_base
            # ==========================================================
            # 优先尝试从存档的原始路径获取文件名（最稳妥，防止文件名已经是 _1024px 导致再次叠加）
            if "tot_original_path" in img:
                raw_filepath = img["tot_original_path"]
            else:
                raw_filepath = img.filepath_from_user()

            # 获取文件名 (例如 "Wood.jpg")
            file_name = os.path.basename(raw_filepath)
            if not file_name: file_name = img.name  # 防空回退

            # 去除后缀 (例如 "Wood") -> 这就是 clean_name_base
            clean_name_base, _ = os.path.splitext(file_name)
            # ==========================================================

            # --- 情况 A: 切换回原图 ---
            if target == 'ORIGINAL':
                # 只有当图片有“存档记录”时才能恢复
                if "tot_original_path" in img:
                    orig_path = img["tot_original_path"]

                    # 转绝对路径检查是否存在

                    # 转绝对路径检查是否存在
                    abs_orig_path = bpy.path.abspath(orig_path)


                    if os.path.exists(abs_orig_path):
                        img.filepath = orig_path
                        img.reload()
                        switched_count += 1
                    else:
                        print(f"[TOT] Original file missing: {abs_orig_path}")
                else:
                    pass

            # --- 情况 B: 切换到指定分辨率 (如 1024 或 camera_optimized) ---
            # --- 情况 B: 切换到指定分辨率 (如 1024 或 camera_optimized) ---
            else:
                # 构造目标文件夹路径
                if target == "camera_optimized":
                    folder_name = "textures_camera_optimized"
                else:
                    folder_name = f"textures_{target}px"


                target_dir_abs = os.path.join(base_path, folder_name)


                found_file = None


                if os.path.exists(target_dir_abs):
                    # 遍历该文件夹下的所有文件，寻找匹配 clean_name_base 的文件
                    # 现在的逻辑：只要文件名里包含 base name 就可以
                    # 更严谨的逻辑建议：startswith(clean_name_base + "_")
                    # 现在的逻辑：只要文件名里包含 base name 就可以
                    # 更严谨的逻辑建议：startswith(clean_name_base + "_")
                    for f in os.listdir(target_dir_abs):
                        # [修复] 更严谨的匹配逻辑
                        # 确保匹配的是 "Wood_..." 而不是 "WoodFloor_..."
                        # 我们生成的文件名格式是: {base}_{size}px.{ext}
                        # 所以文件名必须以 "{base}_" 开头

                        check_prefix = clean_name_base + "_"

                        if f.startswith(check_prefix):
                            # 再检查是否真的包含这个 base (其实 startswith 已经够了，但为了保险)
                            found_file = f
                            break
                        # [修复] 更严谨的匹配逻辑
                        # 确保匹配的是 "Wood_..." 而不是 "WoodFloor_..."
                        # 我们生成的文件名格式是: {base}_{size}px.{ext}
                        # 所以文件名必须以 "{base}_" 开头

                        check_prefix = clean_name_base + "_"

                        if f.startswith(check_prefix):
                            # 再检查是否真的包含这个 base (其实 startswith 已经够了，但为了保险)
                            found_file = f
                            break
                if found_file:
                    # 拼接相对路径
                    # 注意：Windows下有时需要处理路径分隔符，但 Blender 内部通常能处理 /
                    # 拼接相对路径
                    # 注意：Windows下有时需要处理路径分隔符，但 Blender 内部通常能处理 /
                    rel_path = f"//{folder_name}/{found_file}"

                    # [关键] 真正执行切换的地方

                    # [关键] 真正执行切换的地方
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
    """【多线程版】根据相机视角自动计算并生成优化贴图"""
    bl_idname = "tot.optimize_by_camera"
    bl_label = "Optimize by Camera (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []       # 待处理任务数据 (img, req_px)
    _active_threads = [] # 正在运行的线程
    _result_queue = None # 结果队列
    
    _processed = 0    # 已完成数量
    _total_tasks = 0  # 总任务数
    _output_dir = ""  # 输出路径
    
    # 状态变量
    _phase = 'INIT'   # INIT -> ANALYZING -> PROCESSING -> FINISHED

    # 配置
    MAX_THREADS = 4       # 并发线程数
    TIME_BUDGET = 0.02    # 主线程每帧的时间预算

    def modal(self, context, event):
        if event.type == 'TIMER':
            # --- 阶段 1: 分析阶段 (主线程运行，很快) ---
            if self._phase == 'ANALYZING':
                self.do_analysis(context)
                self._phase = 'PROCESSING'
                # 初始化线程队列
                self._result_queue = queue.Queue()
                self._active_threads = []
                context.window_manager.progress_begin(0, self._total_tasks)
                return {'RUNNING_MODAL'}

            # --- 阶段 2: 处理阶段 (多线程调度) ---
            elif self._phase == 'PROCESSING':
                
                # A. 处理已完成的线程结果 (主线程回调)
                while self._result_queue and not self._result_queue.empty():
                    try:
                        res = self._result_queue.get_nowait()
                        self.handle_pil_result(res)
                        self._processed += 1
                    except queue.Empty:
                        break
                
                # B. 清理僵尸线程
                self._active_threads = [t for t in self._active_threads if t.is_alive()]
                
                # C. 检查是否全部完成
                if not self._queue and not self._active_threads:
                    self._phase = 'FINISHED'
                
                # D. 分发新任务
                start_time = time.time()
                
                while self._queue:
                    # 1. 检查时间预算 (给 UI 喘息机会) 和 线程池容量
                    if (time.time() - start_time) > self.TIME_BUDGET:
                        break
                    if len(self._active_threads) >= self.MAX_THREADS:
                        break
                        
                    # 2. 取出一个原始请求
                    img, req_px = self._queue.pop(0)
                    
                    # 3. 准备任务数据 (计算尺寸、路径等)
                    # 如果返回 None，说明被跳过或缓存命中了
                    task_data = self.prepare_task_data(img, req_px)
                    
                    if not task_data:
                        self._processed += 1 # 视为已处理
                        continue
                        
                    # 4. 根据方法分发
                    if task_data["method"] == "PIL":
                        t = threading.Thread(target=pil_resize_worker, args=(task_data, self._result_queue))
                        t.daemon = True
                        t.start()
                        self._active_threads.append(t)
                    else:
                        # 原生处理 (在主线程同步执行)
                        try:
                            # 借用 ResizeImagesAsync 的原生处理逻辑，或者简单的处理
                            # 这里为了代码复用，简单实现一个原生调用
                            self.process_native_fallback(task_data)
                        except Exception as e:
                            print(f"Native Error: {e}")
                        self._processed += 1

                # 更新进度条
                context.window_manager.progress_update(self._processed)
            
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

    def do_analysis(self, context):
        """分析场景，构建任务队列 (保持原逻辑不变)"""
        scn = context.scene.tot_props
        cam = scn.lod_camera or context.scene.camera

        if scn.resize_size == 'c':
            user_max_cap = scn.custom_resize_size
            user_max_cap = scn.custom_resize_size
        else:
            try: user_max_cap = int(scn.resize_size)
            except: user_max_cap = 4096

        ABSOLUTE_MIN_FLOOR = 32
        image_res_map = {}
        
        # 获取所有可见网格
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and not o.hide_render]


        for obj in mesh_objs:
            # 计算物体在屏幕上的像素大小
            px_size, visible = utils.calculate_screen_coverage(context.scene, obj, cam)
            
            if not visible:
                target_res = 32 # 不可见物体给最低分辨率
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
                            
                            # 记录最大需求
                            current_max = image_res_map.get(img, 0)
                            if target_res > current_max:
                                image_res_map[img] = target_res
        
        # 转换为列表
        for img, req_px in image_res_map.items():
            self._queue.append((img, req_px))
            
        self._total_tasks = len(self._queue)
        print(f"[TOT] Analysis complete. {self._total_tasks} textures to process.")

    def prepare_task_data(self, img, req_px):
        """
        核心逻辑：计算最终尺寸、生成路径、判断是否需要处理
        返回 task_dict 或者 None (如果跳过)
        """
        # 1. 计算 Power of 2 尺寸 (保持原有逻辑)
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
        
        # 限制不超过原图
        orig_w = img.size[0]
        orig_h = img.size[1]
        max_orig = max(orig_w, orig_h)
        if final_size > max_orig: final_size = max_orig
        if final_size < 4: final_size = 4

        # 2. 构造文件名和路径
        if "tot_original_path" not in img:
            img["tot_original_path"] = img.filepath

        original_filepath = img.filepath_from_user()
        file_name = os.path.basename(original_filepath)
        if not file_name: file_name = f"{img.name}.png"
        name_part, ext_part = os.path.splitext(file_name)
        if not ext_part: ext_part = ".png"

        new_file_name = f"{name_part}_{final_size}px{ext_part}"
        new_full_path = os.path.join(self._output_dir, new_file_name)

        # 3. 智能缓存检查 (如果文件已存在，直接重连，不生成任务)
        if os.path.exists(new_full_path):
            img.filepath = new_full_path
            img.reload()
            return None # 任务结束，无需入队

        # 4. 决定处理方式 (PIL vs Native, RESIZE vs COPY)
        method = "NATIVE"
        action = "RESIZE" # 默认动作

        # 获取真实后缀
        ext = ext_part.lower()
        if img.filepath:
            ext = os.path.splitext(img.filepath)[1].lower()

        # [HDR/EXR 保护]：强制 COPY 模式
        if ext in {'.exr', '.hdr'}:
            method = "PIL"
            action = "COPY"
        elif HAS_PIL:
            if not img.packed_file and img.filepath:
                 abs_path = bpy.path.abspath(img.filepath)
                 if os.path.exists(abs_path):
                     method = "PIL"
        
        # 构造任务包
        task_data = {
            "img_name": img.name,
            "target_size": final_size,
            "src_path": bpy.path.abspath(img.filepath), 
            "dst_path": new_full_path,
            "method": method,
            "action": action 
        }
        return task_data

    def handle_pil_result(self, res):
        """处理 PIL 线程的回调结果"""
        img = bpy.data.images.get(res["img_name"])
        if not img: return
        
        if res["status"] in {"SUCCESS", "COPIED"}:
            try:
                # 只有当路径真正改变时才设置
                if hasattr(img, "filepath") and "dst_path" in res:
                    rel_path = bpy.path.relpath(res["dst_path"])
                    img.filepath = rel_path
                img.reload()
            except Exception as e:
                print(f"Reload Error: {e}")
        else:
            print(f"PIL Failed for {img.name}: {res.get('error')}")

    def process_native_fallback(self, task):
        """原生 API 兜底 (借用 ResizeImagesAsync 的逻辑思想)"""
        # 注意：这里需要重新获取 Image 对象，因为是在主线程调用的
        img = bpy.data.images.get(task["img_name"])
        if not img: return
        
        target_size = task["target_size"]
        new_full_path = task["dst_path"]
        
        # 简单检查尺寸
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
                render.color_mode = 'RGBA' # 确保透明
            img.save_render(filepath=new_full_path)
        finally:
            render.file_format = old_fmt
            render.color_mode = old_mode
            
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        bpy.ops.tot.updateimagelist()

        # Purge
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