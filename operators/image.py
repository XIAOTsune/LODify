import os
import re
import bpy
import shutil
from .. import utils 
import time
import gc

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
            # 检查文件扩展名，如果是 exr 或 hdr，直接跳过，不让它进入列表
            if img.filepath:
                ext = os.path.splitext(img.filepath)[1].lower()
                if ext in {'.exr', '.hdr'}:
                    continue

            # 也可以检查它是否被 World 环境使用 (双重保险)
            is_world_tex = False
            if bpy.context.scene.world and bpy.context.scene.world.node_tree:
                for n in bpy.context.scene.world.node_tree.nodes:
                    if n.type == 'TEX_ENVIRONMENT' and n.image == img:
                        is_world_tex = True
                        break
            if is_world_tex: continue
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
        if not img: return

        # HDR 格式锁
        # 如果是 HDR/EXR，绝对禁止处理，直接返回
        # 即使这里不返回，下面的 save_render 也会破坏线性空间的光照数据
        if img.filepath:
            ext = os.path.splitext(img.filepath)[1].lower()
            if ext in {'.exr', '.hdr'}:
                print(f"[TOT] Skipped HDR/EXR: {img.name}")
                return


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
        
        # 2. 内存缩放(带保护)
        # 检查原图尺寸
        orig_w = img.size[0]
        orig_h = img.size[1]

        # 只有当原图比目标尺寸大时，才进行缩放
        # 如果原图(256) < 目标(1024)，则不缩放，直接按原样保存
        should_resize = (orig_w > target_size) or (orig_h > target_size)

        if should_resize:
            img.scale(target_size, target_size)
            # 注意：scale 操作会直接修改内存中的图像数据
        else:
            # 不执行 scale，直接保存就是“复制”的效果
            # 但文件名依然保留 _1024px 后缀，方便统一管理和切换逻辑
            pass

        #################
        # 3. 物理保存 (带格式保护)
        # 使用 bpy.context.scene 确保能获取到场景
        render_settings = bpy.context.scene.render.image_settings

        # 1. 备份当前场景的渲染设置
        old_file_format = render_settings.file_format
        old_color_mode = render_settings.color_mode
        old_depth = render_settings.color_depth

        # 2. 根据文件后缀强行指定格式
        ext = os.path.splitext(new_full_path)[1].lower()

        if ext in ['.jpg', '.jpeg']:
            render_settings.file_format = 'JPEG'
            render_settings.color_mode = 'RGB'  # 强制 RGB 省空间
        elif ext == '.png':
            render_settings.file_format = 'PNG'
            render_settings.color_mode = 'RGBA'  # 默认保留 Alpha
        # 你可以在这里加更多格式支持，比如 .tga, .bmp 等

        try:
            # 3. 执行保存
            img.save_render(filepath=new_full_path)
        finally:
            # 4. 无论是否报错，必须还原用户的设置
            render_settings.file_format = old_file_format
            render_settings.color_mode = old_color_mode
            render_settings.color_depth = old_depth
        # ================================================================

        # 4. 重连并刷新
        img.filepath = new_full_path
        img.reload()

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # 刷新列表 UI
        bpy.ops.tot.updateimagelist()
        # 运行多次以确保级联引用的数据都被清理干净
        print("[TOT] Purging unused data blocks...")
        for _ in range(3):
            try:
                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
            except AttributeError:
                # 兼容旧版本 API (如果有必要)
                if hasattr(bpy.data, 'purge_unused_data'):
                    bpy.data.purge_unused_data()
                break
            except Exception:
                break
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

            # --- 情况 A: 切换回原图 ---
            if target == 'ORIGINAL':
                # 只有当图片有“存档记录”时才能恢复
                if "tot_original_path" in img:
                    orig_path = img["tot_original_path"]

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
                if found_file:
                    # 拼接相对路径
                    # 注意：Windows下有时需要处理路径分隔符，但 Blender 内部通常能处理 /
                    rel_path = f"//{folder_name}/{found_file}"

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

        # 1. 获取用户设置的【上限】(Max Cap)
        # 之前这里逻辑反了，现在我们将它作为最大值
        if scn.resize_size == 'c':
            user_max_cap = scn.custom_resize_size
        else:
            try:
                user_max_cap = int(scn.resize_size)
            except:
                user_max_cap = 4096  # 如果读取失败，给一个默认的大上限

        # 定义一个绝对死线（下限），防止贴图变成 1x1 像素看不清
        ABSOLUTE_MIN_FLOOR = 32

        image_res_map = {}
        mesh_objs = [o for o in context.scene.objects if o.type == 'MESH' and not o.hide_render]

        for obj in mesh_objs:
            # 计算物体在屏幕上的像素大小
            px_size, visible = utils.calculate_screen_coverage(context.scene, obj, cam)
            if not visible:
                # 之前是 continue (跳过优化，保留原图 -> 导致显存不降)
                # 现在的策略：看不见的物体，直接给个最低分辨率 (比如 32px)
                # 这样既省显存，又不怕穿帮
                target_res = 32
            else:
                # 可见的物体，走原来的计算逻辑
                # [cite_start]基础算法：屏幕占比 * 1.2 (稍微留点余量) [cite: 226]
                calculated_res = px_size * 1.2

                # [cite_start]1. 下限保护：不能小于 32px [cite: 227]
                target_res = max(calculated_res, ABSOLUTE_MIN_FLOOR)

                # [cite_start]2. 上限截断：不能超过用户设置的尺寸 [cite: 227]
                target_res = min(target_res, user_max_cap)
            # =================================================

            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            img = node.image
                            if img.source in {'VIEWER', 'GENERATED'}: continue

                            # 记录该图片在所有物体中需要的最大分辨率
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
        # hdr保护
        if img.filepath:
            ext = os.path.splitext(img.filepath)[1].lower()
            if ext in {'.exr', '.hdr'}:
                print(f"[TOT] Skipped HDR/EXR in Auto-Opt: {img.name}")
                return
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
                # 1. 只有当 目标尺寸 < 原图尺寸 时才执行缩放
                # 如果相等 (final_size == max_orig)，说明不需要缩小，直接保存原图数据即可
                if final_size < max_orig:
                    img.scale(final_size, final_size)
                ######
                # 使用 bpy.context.scene
                render_settings = bpy.context.scene.render.image_settings

                # A. 备份
                old_file_format = render_settings.file_format
                old_color_mode = render_settings.color_mode
                old_depth = render_settings.color_depth

                # B. 设置
                ext = os.path.splitext(new_full_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    render_settings.file_format = 'JPEG'
                    render_settings.color_mode = 'RGB'
                elif ext == '.png':
                    render_settings.file_format = 'PNG'
                    render_settings.color_mode = 'RGBA'

                try:
                    # C. 保存
                    img.save_render(filepath=new_full_path)
                finally:
                    # D. 还原
                    render_settings.file_format = old_file_format
                    render_settings.color_mode = old_color_mode
                    render_settings.color_depth = old_depth
                # ========================================================

                # 3. 重连
                img.filepath = new_full_path
                img.reload()

        except Exception as e:
            print(f"Error processing {img.name}: {e}")

    def finish(self, context):
        """结束清理"""
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        bpy.ops.tot.updateimagelist()

        print("[TOT] Running Orphan Purge...")
        for _ in range(3):  # 运行几次以确保级联引用的都被清掉
            # 这里使用 outliner.orphans_purge 是假设你的 Blender 版本支持此操作符
            # 如果你的版本不支持，可能需要手动调用 bpy.data.purge_unused_data()
            try:
                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
            except AttributeError:
                # 如果操作符不存在，尝试使用 data.purge_unused_data
                if hasattr(bpy.data, 'purge_unused_data'):
                    bpy.data.purge_unused_data()
                break
        # 强制回收 Python 层的垃圾内存
        gc.collect()
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