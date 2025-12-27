import bpy
import time
from mathutils import Vector

class LOD_OT_ShaderLODUpdateAsync(bpy.types.Operator):
    """异步更新材质 Shader 细节 (法线/置换)"""
    bl_idname = "lod.shader_lod_update_async"
    bl_label = "Update Shader LOD (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []
    _total_tasks = 0
    _processed = 0
    _updated_count = 0
    
    # 时间预算 (秒)
    TIME_BUDGET = 0.05 

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._queue:
                return self.finish(context)
            
            start_time = time.time()
            
            # --- 时间片循环 ---
            while self._queue:
                # 取出 (obj, lod_level) 元组
                obj, level = self._queue.pop(0)
                
                try:
                    self.process_object_material(context, obj, level)
                except Exception as e:
                    print(f"Shader LOD Error on {obj.name}: {e}")
                
                self._processed += 1
                
                if (time.time() - start_time) > self.TIME_BUDGET:
                    break
            
            context.window_manager.progress_update(self._processed)
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.lod_props
        if not scn.exp_shader_lod_enabled:
            self.report({'WARNING'}, "Enable 'Shader LOD' first.")
            return {'CANCELLED'}

        cam = scn.lod_camera or context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No Camera found.")
            return {'CANCELLED'}
        
        cam_loc = cam.matrix_world.translation
        d0, d1, d2 = scn.lod_dist_0, scn.lod_dist_1, scn.lod_dist_2
        
        # 1. 构建任务队列
        self._queue = []
        
        # 预先获取所有可见 Mesh
        for obj in context.scene.objects:
            if obj.type != 'MESH' or obj.hide_viewport: continue
            if not obj.material_slots: continue
            
            # 计算距离
            try:
                # 简单计算中心点距离
                center = obj.matrix_world.translation
                dist = (center - cam_loc).length
            except:
                continue
            
            # 判定 Level
            level = 0
            if dist <= d0: level = 0
            elif dist <= d1: level = 1
            elif dist <= d2: level = 2
            else: level = 3
            
            self._queue.append((obj, level))

        if not self._queue:
            self.report({'WARNING'}, "No suitable objects found.")
            return {'CANCELLED'}

        # 2. 初始化
        self._total_tasks = len(self._queue)
        self._processed = 0
        self._updated_count = 0
        
        # 缓存乘数参数
        self.n_mults = [1.0, scn.exp_normal_mult_1, scn.exp_normal_mult_2, scn.exp_normal_mult_3]
        self.d_mults = [1.0, scn.exp_disp_mult_1, scn.exp_disp_mult_2, scn.exp_disp_mult_3]

        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def process_object_material(self, context, obj, level):
        """处理单个物体的所有材质 (优化版：智能跳过无效节点)"""
        
        target_n_mult = self.n_mults[level]
        target_d_mult = self.d_mults[level]
        
        modified = False

        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes or not mat.node_tree: continue
            
            # 遍历节点
            for node in mat.node_tree.nodes:
                
                # --- A. 处理法线节点 (Normal Map) ---
                if node.type == 'NORMAL_MAP':
                    # [优化] 1. 检查是否有贴图输入
                    # 如果 "Color" 接口没连线，说明这是一个无效/纯色的法线节点，直接跳过
                    if not node.inputs['Color'].is_linked:
                        continue

                    # 检查 Strength 输入
                    socket = node.inputs.get('Strength')
                    # 只处理未被其他节点控制的 Strength (即没有连线到 Strength)
                    if socket and not socket.is_linked: 
                        
                        # [优化] 2. 只有当原始值大于 0 时才处理 (本来就是0就没必要算了)
                        # 第一次读取时存档
                        if "lod_orig_val" not in node:
                            if socket.default_value <= 0.001: # 原始值极小，视为无效
                                continue
                            node["lod_orig_val"] = socket.default_value
                        
                        # 2. 计算新值
                        orig_val = node["lod_orig_val"]
                        new_val = orig_val * target_n_mult
                        
                        # 3. 应用 (减少不必要的 update_tag 调用)
                        if abs(socket.default_value - new_val) > 0.001:
                            socket.default_value = new_val
                            modified = True

                # --- B. 处理置换节点 (Displacement) ---
                elif node.type == 'DISPLACEMENT':
                    # [优化] 1. 检查是否有高度输入
                    # 如果 "Height" (或有的版本叫 Normal) 没连线，跳过
                    height_socket = node.inputs.get('Height')
                    if not height_socket or not height_socket.is_linked:
                        continue

                    # 检查 Scale 输入
                    socket = node.inputs.get('Scale')
                    if socket and not socket.is_linked:
                        
                        if "lod_orig_val" not in node:
                            if socket.default_value <= 0.001:
                                continue
                            node["lod_orig_val"] = socket.default_value
                        
                        orig_val = node["lod_orig_val"]
                        new_val = orig_val * target_d_mult
                        
                        if abs(socket.default_value - new_val) > 0.001:
                            socket.default_value = new_val
                            modified = True

        if modified:
            self._updated_count += 1

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        self.report({'INFO'}, f"Shader LOD Updated: {self._updated_count} materials adjusted.")
        return {'FINISHED'}


class LOD_OT_ShaderLODReset(bpy.types.Operator):
    """恢复材质原始参数"""
    bl_idname = "lod.shader_lod_reset"
    bl_label = "Reset Shader Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        count = 0
        for mat in bpy.data.materials:
            if not mat.use_nodes or not mat.node_tree: continue
            
            for node in mat.node_tree.nodes:
                if "lod_orig_val" in node:
                    # 恢复数值
                    if node.type == 'NORMAL_MAP':
                        if not node.inputs['Strength'].is_linked:
                            node.inputs['Strength'].default_value = node["lod_orig_val"]
                    elif node.type == 'DISPLACEMENT':
                        if not node.inputs['Scale'].is_linked:
                            node.inputs['Scale'].default_value = node["lod_orig_val"]
                    
                    # 移除标记 (可选，或者保留以便下次用)
                    # del node["lod_orig_val"] 
                    count += 1
                    
        self.report({'INFO'}, f"Reset {count} shader nodes to original values.")
        return {'FINISHED'}

classes = (
    LOD_OT_ShaderLODUpdateAsync,
    LOD_OT_ShaderLODReset,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)