import bpy
import time
import math
from mathutils import Vector
from .. import utils

# =============================================================================
# 常量定义
# =============================================================================
DECIMATE_MOD_NAME = "TOT_LOD_DECIMATE"
GEO_NODES_MOD_NAME = "TOT_GEO_LOD"
GN_INPUT_FACTOR = "LOD_Factor"      # 接口1：强度
GN_INPUT_ANGLE = "Angle_Threshold" 
GN_INPUT_MAX_DIST = "Max_Merge_Dist" # 接口2：角度阈值

# =============================================================================
# Helper: 几何节点组构建
# =============================================================================
# =============================================================================
# Helper: 几何节点组构建 (修复版)
# =============================================================================
def ensure_lod_node_group():
    """
    创建/更新 LOD 节点组 (Geometry Nodes) - V3 空间塌陷版 (修复兼容性)
    """
    name = "TOT_GEO_LOD_Advanced" 
    group = bpy.data.node_groups.get(name)
    
    if not group:
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")

    # --- 内嵌辅助函数：安全创建节点 (恢复原逻辑) ---
    def safe_create_node(nodes, possible_names, label=None):
        for node_name in possible_names:
            try:
                node = nodes.new(node_name)
                if label: node.label = label
                return node
            except Exception:
                continue
        return None
    # -----------------------------------------------------------

    # 1. 定义接口
    if hasattr(group, "interface"):
        group.interface.clear()
        group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        
        # [Input] LOD_Factor
        s1 = group.interface.new_socket(name=GN_INPUT_FACTOR, in_out='INPUT', socket_type='NodeSocketFloat')
        s1.min_value = 0.0
        s1.max_value = 1.0
        s1.default_value = 1.0
        
        # [Input] Max_Merge_Dist
        s2 = group.interface.new_socket(name=GN_INPUT_MAX_DIST, in_out='INPUT', socket_type='NodeSocketFloat')
        s2.min_value = 0.0
        s2.default_value = 0.5 
        
        # [Output] Geometry
        group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = group.nodes
    links = group.links
    nodes.clear()

    # 2. 构建节点图
    n_in = nodes.new("NodeGroupInput")
    n_in.location = (-800, 0)
    
    n_out = nodes.new("NodeGroupOutput")
    n_out.location = (600, 0)
    
    # --- 核心修复 A: 使用 safe_create_node 创建 Merge 节点 ---
    n_merge = safe_create_node(
        nodes, 
        ["GeometryNodeMergeByDistance", "GeometryNodeMeshMergeByDistance"], 
        label="Merge by Distance"
    )
    if not n_merge:
        # 如果连这个最基本的节点都创建失败，说明环境有问题
        raise RuntimeError("Missing Merge Node: Could not create MergeByDistance node.")
        
    n_merge.location = (200, 0)
    
    # --- 核心修复 B: 安全设置属性 ---
    try:
        n_merge.mode = 'ALL' # 尝试设置为“合并所有”
    except AttributeError:
        # 如果报错说没有 mode 属性，说明是旧版节点，默认就是合并所有，直接忽略
        pass 

    # --- 逻辑 A: 指数级距离控制 ---
    n_invert = nodes.new("ShaderNodeMath")
    n_invert.operation = 'SUBTRACT'
    n_invert.label = "Invert Factor"
    n_invert.inputs[0].default_value = 1.0
    n_invert.location = (-600, 100)
    
    n_power = nodes.new("ShaderNodeMath")
    n_power.operation = 'POWER'
    n_power.label = "Exponential Curve"
    n_power.inputs[1].default_value = 3.0
    n_power.location = (-400, 100)
    
    n_mult_dist = nodes.new("ShaderNodeMath")
    n_mult_dist.operation = 'MULTIPLY'
    n_mult_dist.label = "Calc Distance"
    n_mult_dist.location = (-200, 100)
    
    # --- 逻辑 B: 动态边缘保护 ---
    # 使用 safe_create_node 寻找 Edge Angle 节点
    n_edge_angle = safe_create_node(
        nodes, 
        [
            "GeometryNodeInputMeshEdgeAngle", 
            "GeometryNodeEdgeAngle", 
            "GeometryNodeMeshEdgeAngle", 
            "GeometryNodeInputEdgeAngle"
        ],
        label="Edge Angle"
    )
    
    n_map_angle = nodes.new("ShaderNodeMapRange")
    n_map_angle.label = "Dynamic Threshold"
    n_map_angle.location = (-400, -300)
    n_map_angle.inputs['From Min'].default_value = 0.0
    n_map_angle.inputs['From Max'].default_value = 1.0
    n_map_angle.inputs['To Min'].default_value = 3.14159
    n_map_angle.inputs['To Max'].default_value = 0.05
    
    n_compare = nodes.new("FunctionNodeCompare")
    n_compare.data_type = 'FLOAT'
    n_compare.operation = 'LESS_THAN'
    n_compare.label = "Selection Mask"
    n_compare.location = (-200, -200)

    # 3. 连线
    links.new(n_in.outputs[0], n_merge.inputs[0])       # Geo -> Merge
    links.new(n_merge.outputs[0], n_out.inputs[0])      # Merge -> Output
    
    # 距离逻辑
    links.new(n_in.outputs[GN_INPUT_FACTOR], n_invert.inputs[1])
    links.new(n_invert.outputs[0], n_power.inputs[0])
    links.new(n_power.outputs[0], n_mult_dist.inputs[0])
    links.new(n_in.outputs[GN_INPUT_MAX_DIST], n_mult_dist.inputs[1])
    links.new(n_mult_dist.outputs[0], n_merge.inputs['Distance'])
    
    # 只有当 Edge Angle 节点创建成功时，才连接 Selection 逻辑
    if n_edge_angle:
        try:
            links.new(n_in.outputs[GN_INPUT_FACTOR], n_map_angle.inputs['Value'])
            links.new(n_edge_angle.outputs[0], n_compare.inputs[0])
            links.new(n_map_angle.outputs[0], n_compare.inputs[1])
            
            # 尝试获取 Selection 接口
            sel_socket = n_merge.inputs.get("Selection")
            if not sel_socket and len(n_merge.inputs) > 1:
                sel_socket = n_merge.inputs[1] # 盲猜第二个接口
            
            if sel_socket:
                links.new(n_compare.outputs[0], sel_socket)
        except Exception as e:
            print(f"TOT Warning: Could not connect selection logic: {e}")
            pass

    return group

def get_input_identifier(node_group, input_name):
    """(辅助函数保持不变)"""
    if not node_group: return None
    if hasattr(node_group, "interface"):
        for item in node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == input_name:
                    return item.identifier
    elif hasattr(node_group, "inputs"):
        for input_socket in node_group.inputs:
            if input_socket.name == input_name:
                return input_socket.identifier
    return None

# =============================================================================
# Operators
# =============================================================================

class TOT_OT_GeoLODSetup(bpy.types.Operator):
    """Setup Geometry LOD Modifiers (Async Version)"""
    bl_idname = "tot.geo_lod_setup"
    bl_label = "Setup Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    # --- 异步相关变量 ---
    _timer = None
    _queue = []
    _total_tasks = 0
    _processed = 0
    _created_count = 0
    
    # 每一帧允许运行的时间 (秒)，类似 UpdateAsync
    TIME_BUDGET = 0.05 

    def modal(self, context, event):
        if event.type == 'TIMER':
            # 如果队列为空，结束
            if not self._queue:
                return self.finish(context)
            
            start_time = time.time()
            
            # --- 时间片循环 ---
            while self._queue:
                obj = self._queue.pop(0)
                
                try:
                    self.process_object(obj)
                except Exception as e:
                    print(f"Setup Error on {obj.name}: {e}")
                
                self._processed += 1
                
                # 超时则暂停，把控制权还给界面
                if (time.time() - start_time) > self.TIME_BUDGET:
                    break
            
            # 更新进度条
            context.window_manager.progress_update(self._processed)
            
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.tot_props
        self.method = scn.geo_lod_method
        self.min_faces = scn.geo_lod_min_faces
        self.max_dist = scn.geo_lod_max_dist
        
        # 1. 预先准备资源 (避免在循环中重复检查)
        self.lod_group = None
        if self.method == 'GNODES':
            try:
                # 确保节点组存在
                self.lod_group = ensure_lod_node_group()
                # 预先获取接口 ID，避免每处理一个物体都去遍历查找
                self.gn_id_dist = get_input_identifier(self.lod_group, GN_INPUT_MAX_DIST)
            except Exception as e:
                self.report({'ERROR'}, f"Create Node Error: {e}")
                return {'CANCELLED'}
        # [新增] 1.1 预先计算实例源黑名单
        self.instance_sources = utils.get_instance_sources(context.scene)
        if self.instance_sources:
             print(f"[TOT] Detected {len(self.instance_sources)} instance source objects. They will be skipped.")
      
        # 2. 构建任务队列
        self._queue = []
        # 遍历场景所有物体
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue

            #  如果是实例源，跳过优化（保护母体）
            if obj in self.instance_sources:
                continue            
            # 面数过滤
            if self.min_faces > 0 and len(obj.data.polygons) < self.min_faces: continue
            
            self._queue.append(obj)
        
        if not self._queue:
            self.report({'WARNING'}, "No eligible mesh objects found.")
            return {'CANCELLED'}

        # 3. 初始化状态
        self._total_tasks = len(self._queue)
        self._processed = 0
        self._created_count = 0
        
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        self.report({'INFO'}, f"Starting Setup for {self._total_tasks} objects...")
        return {'RUNNING_MODAL'}

    def process_object(self, obj):
        """单个物体的处理逻辑 (从原 execute 提取)"""
        
        if self.method == 'DECIMATE':
            # 如果存在 GN 修改器则移除 (互斥逻辑)
            if obj.modifiers.get(GEO_NODES_MOD_NAME):
                obj.modifiers.remove(obj.modifiers.get(GEO_NODES_MOD_NAME))
            
            mod = obj.modifiers.get(DECIMATE_MOD_NAME)
            if not mod:
                mod = obj.modifiers.new(DECIMATE_MOD_NAME, 'DECIMATE')
                mod.decimate_type = 'COLLAPSE'
                mod.ratio = 1.0 # 初始设为 1.0，防止刚加上去模型就消失
                obj["_tot_geo_lod_created"] = True
                self._created_count += 1
                
        elif self.method == 'GNODES':
            # 如果存在 Decimate 修改器则移除
            if obj.modifiers.get(DECIMATE_MOD_NAME):
                obj.modifiers.remove(obj.modifiers.get(DECIMATE_MOD_NAME))

            mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
            force_rebuild = False
            
            # 检查是否使用了旧版节点组
            if mod and mod.node_group and mod.node_group.name != "TOT_GEO_LOD_Advanced":
                force_rebuild = True
            # 检查接口数量
            if mod and mod.node_group and self.lod_group and \
               len(mod.node_group.interface.items_tree) != len(self.lod_group.interface.items_tree):
                force_rebuild = True

            if not mod or force_rebuild:
                if mod: obj.modifiers.remove(mod)
                mod = obj.modifiers.new(name=GEO_NODES_MOD_NAME, type='NODES')
                mod.node_group = self.lod_group
                obj["_tot_geo_lod_created"] = True
                self._created_count += 1
            
            # 初始化参数
            if self.gn_id_dist:
                mod[self.gn_id_dist] = self.max_dist 

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        
        # 强制刷新视图
        for win in context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D': area.tag_redraw()
                
        self.report({'INFO'}, f"Setup complete: {self._created_count} modifiers updated/created.")
        return {'FINISHED'}

class TOT_OT_GeoLODUpdateAsync(bpy.types.Operator):
    """
    现在 Python 只需要计算 Factor，无需计算 Angle
    """
    bl_idname = "tot.geo_lod_update_async"
    bl_label = "Update Geometry (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []
    _total_tasks = 0
    _processed = 0
    _updated_count = 0
    TIME_BUDGET = 0.05

    def modal(self, context, event):
        if event.type == 'TIMER':
            if not self._queue: return self.finish(context)
            start_time = time.time()
            while self._queue:
                obj = self._queue.pop(0)
                try: self.process_object(context, obj)
                except: pass
                self._processed += 1
                if (time.time() - start_time) > self.TIME_BUDGET: break
            context.window_manager.progress_update(self._processed)
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.tot_props
        if not scn.geo_lod_enabled: return {'CANCELLED'}
        self.cam = scn.lod_camera or context.scene.camera
        if not self.cam: 
            self.report({'ERROR'}, "No Camera found.")
            return {'CANCELLED'}
            
        method = scn.geo_lod_method
        target_mod = DECIMATE_MOD_NAME if method == 'DECIMATE' else GEO_NODES_MOD_NAME
        
        # 获取黑名单
        skipped_sources = utils.get_instance_sources(context.scene)   

        self._queue = []
        for obj in context.scene.objects:
            if obj.type == 'MESH' and not obj.hide_viewport:
                # 如果是实例源就跳过计算
                if obj in skipped_sources:
                    continue

                if obj.modifiers.get(target_mod):
                    self._queue.append(obj)
        
        if not self._queue:
            self.report({'WARNING'}, "Run 'Setup' first.")
            return {'CANCELLED'}

        self._total_tasks = len(self._queue)
        self._processed = 0
        self._updated_count = 0
        self.method = method
        
        # 全局参数缓存
        self.min_protection = scn.geo_lod_min_ratio
        self.min_faces = scn.geo_lod_min_faces
        self.max_dist = scn.geo_lod_max_dist # 用户设置的最大塌陷距离
        
        self.gn_id_factor = None
        self.gn_id_dist = None
        
        if method == 'GNODES':
            group = bpy.data.node_groups.get("TOT_GEO_LOD_Advanced")
            self.gn_id_factor = get_input_identifier(group, GN_INPUT_FACTOR)
            self.gn_id_dist = get_input_identifier(group, GN_INPUT_MAX_DIST)

        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window) 
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def process_object(self, context, obj):
        # 1. 面数保护
        is_protected_by_faces = False
        if hasattr(obj.data, "polygons") and len(obj.data.polygons) < self.min_faces:
            is_protected_by_faces = True

        # 2. 计算 Factor
        if is_protected_by_faces:
            target_factor = 1.0
        else:
            if hasattr(utils, 'get_normalized_screen_ratio'):
                raw_ratio = utils.get_normalized_screen_ratio(context.scene, obj, self.cam)
            else:
                raw_ratio = 0.5 
            
            # 使用 Stepped 还是 Linear 取决于你，这里保持 Stepped 更稳定
            if hasattr(utils, 'get_stepped_lod_factor'):
                target_factor = utils.get_stepped_lod_factor(raw_ratio, self.min_protection)
            else:
                target_factor = 1.0

        # 3. 应用到修改器
        EPSILON = 0.001 

        if self.method == 'DECIMATE':
            mod = obj.modifiers.get(DECIMATE_MOD_NAME)
            if mod and abs(mod.ratio - target_factor) > EPSILON:
                mod.ratio = target_factor
                obj.update_tag() 
                self._updated_count += 1
            
        elif self.method == 'GNODES':
            mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
            if mod:
                changed = False
                
                # A. 更新 LOD_Factor (核心)
                if self.gn_id_factor:
                    try:
                        curr = mod.get(self.gn_id_factor, 1.0)
                        if abs(curr - target_factor) > EPSILON:
                            mod[self.gn_id_factor] = target_factor
                            changed = True
                    except: pass
                
                # B. 同步 Max_Dist (允许用户在播放时实时调整最大塌陷程度)
                if self.gn_id_dist:
                    try:
                        curr_dist = mod.get(self.gn_id_dist, 0.5)
                        if abs(curr_dist - self.max_dist) > 0.0001:
                            mod[self.gn_id_dist] = self.max_dist
                            changed = True
                    except: pass
                
                if changed:
                    obj.update_tag() 
                    self._updated_count += 1

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        for win in context.window_manager.windows:
            for area in win.screen.areas:
                if area.type == 'VIEW_3D': area.tag_redraw()
        self.report({'INFO'}, f"Updated {self._updated_count} objects.")
        return {'FINISHED'}
    
class TOT_OT_GeoLODReset(bpy.types.Operator):
    bl_idname = "tot.geo_lod_reset"
    bl_label = "Reset Geometry"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        removed = 0
        for obj in context.scene.objects:
            if obj.modifiers.get(DECIMATE_MOD_NAME): 
                obj.modifiers.remove(obj.modifiers.get(DECIMATE_MOD_NAME)); removed+=1
            if obj.modifiers.get(GEO_NODES_MOD_NAME): 
                obj.modifiers.remove(obj.modifiers.get(GEO_NODES_MOD_NAME)); removed+=1
            if "_tot_geo_lod_created" in obj: del obj["_tot_geo_lod_created"]
        self.report({'INFO'}, f"Reset {removed} objects.")
        return {'FINISHED'}

class TOT_OT_GeoLODApply(bpy.types.Operator):
    bl_idname = "tot.geo_lod_apply"
    bl_label = "Apply (Destructive)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        # 确定要应用哪个修改器名字
        target_mod_name = "TOT_LOD_DECIMATE" if scn.geo_lod_method == 'DECIMATE' else "TOT_GEO_LOD"

        applied_count = 0

        # 必须在 Object 模式下才能应用修改器
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 获取当前选中的物体，或者处理全场景？
        # 通常 Apply 操作是对当前选中的物体，或者是全场景带有该修改器的物体
        # 既然是批量工具，建议处理全场景带有该修改器的物体

        # 备份当前激活物体
        original_active = context.view_layer.objects.active

        for obj in context.scene.objects:
            if obj.type != 'MESH': continue

            mod = obj.modifiers.get(target_mod_name)
            if mod:
                # Blender API 限制：应用修改器必须让该物体成为“Active”
                context.view_layer.objects.active = obj
                try:
                    bpy.ops.object.modifier_apply(modifier=target_mod_name)

                    # 清理标记
                    if "_tot_geo_lod_created" in obj:
                        del obj["_tot_geo_lod_created"]

                    applied_count += 1
                except Exception as e:
                    print(f"Failed to apply for {obj.name}: {e}")

        # 恢复之前的激活物体
        if original_active:
            context.view_layer.objects.active = original_active

        self.report({'INFO'}, f"Applied modifiers on {applied_count} objects.")
        return {'FINISHED'}

classes = (
    TOT_OT_GeoLODSetup,
    TOT_OT_GeoLODUpdateAsync,
    TOT_OT_GeoLODReset,
    TOT_OT_GeoLODApply,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)