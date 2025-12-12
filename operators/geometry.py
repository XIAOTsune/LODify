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
GN_INPUT_ANGLE = "Angle_Threshold"  # 接口2：角度阈值

# =============================================================================
# Helper: 几何节点组构建
# =============================================================================
def ensure_lod_node_group():
    """
    创建/更新 LOD 节点组
    修复: Random Value 节点输出索引错误 (应该是 outputs[3] 对应 Boolean)
    """
    name = "TOT_GEO_LOD_Advanced" 
    group = bpy.data.node_groups.get(name)
    
    if not group:
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    
    # -----------------------------------------------------------
    # 内嵌辅助函数
    # -----------------------------------------------------------
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

    # 1. 定义接口 (Interface)
    if hasattr(group, "interface"):
        group.interface.clear()
        
        # [0] Geometry In
        group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        
        # [1] LOD_Factor
        s1 = group.interface.new_socket(name=GN_INPUT_FACTOR, in_out='INPUT', socket_type='NodeSocketFloat')
        s1.min_value = 0.0
        s1.max_value = 1.0
        s1.default_value = 1.0
        
        # [2] Angle_Threshold
        s2 = group.interface.new_socket(name=GN_INPUT_ANGLE, in_out='INPUT', socket_type='NodeSocketFloat')
        s2.min_value = 0.0
        s2.max_value = 3.14159
        s2.default_value = 1.5 
        
        # [0] Geometry Out
        group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = group.nodes
    links = group.links
    nodes.clear()

    # ===========================================================
    # 2. 创建节点
    # ===========================================================
    
    n_in = nodes.new("NodeGroupInput")
    n_in.location = (-900, 0)
    
    n_out = nodes.new("NodeGroupOutput")
    n_out.location = (600, 0)

    # [Merge By Distance]
    n_merge = safe_create_node(
        nodes, 
        ["GeometryNodeMergeByDistance", "GeometryNodeMeshMergeByDistance"], 
        label="Merge by Distance"
    )
    if not n_merge: raise RuntimeError("Missing Merge Node")
    
    n_merge.inputs["Distance"].default_value = 0.1
    n_merge.location = (300, 0)

    # [Edge Angle]
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

    if n_edge_angle:
        n_edge_angle.location = (-600, 250)

        # [Compare] Is Flat?
        n_is_flat = nodes.new("FunctionNodeCompare")
        n_is_flat.data_type = 'FLOAT'
        n_is_flat.operation = 'LESS_THAN'
        n_is_flat.label = "Is Flat?"
        n_is_flat.location = (-350, 250)

        # [Math] 1.0 - LOD
        n_invert = nodes.new("ShaderNodeMath")
        n_invert.operation = 'SUBTRACT'
        n_invert.label = "1.0 - LOD"
        n_invert.inputs[0].default_value = 1.0
        n_invert.location = (-600, -150)

        # [Random]
        n_random = nodes.new("FunctionNodeRandomValue")
        n_random.data_type = 'BOOLEAN'
        n_random.label = "Random Cull"
        n_random.location = (-350, -150)

        # [Boolean And]
        n_and = nodes.new("FunctionNodeBooleanMath")
        n_and.operation = 'AND'
        n_and.label = "Filter"
        n_and.location = (-100, 100)

        # ===========================================================
        # 3. 连线
        # ===========================================================
        
        # A. Edge Angle -> Compare A
        links.new(n_edge_angle.outputs[0], n_is_flat.inputs[0])

        # B. Input Angle_Threshold -> Compare B
        links.new(n_in.outputs[2], n_is_flat.inputs[1])

        # C. Input LOD_Factor -> Invert Input[1]
        links.new(n_in.outputs[1], n_invert.inputs[1])

        # D. Invert -> Random Probability
        links.new(n_invert.outputs[0], n_random.inputs["Probability"])

        # E. Compare + Random -> And
        links.new(n_is_flat.outputs[0], n_and.inputs[0])
        
        # 【核心修复】：Random Value 的布尔输出是 outputs[3]，不是 [0]
        # outputs[0]=Float, [1]=Vector, [2]=Int, [3]=Boolean
        links.new(n_random.outputs[3], n_and.inputs[1])

        # F. And -> Merge Selection
        try:
            target_socket = n_merge.inputs.get("Selection") or n_merge.inputs[1]
            links.new(n_and.outputs[0], target_socket)
        except: pass
        
    else:
        # 降级模式
        print("[TOT] No Edge Angle node found. Fallback mode.")
        links.new(n_in.outputs[0], n_merge.inputs[0]) 

    # 主几何流
    in_geo = n_in.outputs[0]
    out_geo = n_out.inputs[0]
    merge_geo_in = n_merge.inputs.get("Geometry") or n_merge.inputs[0]
    merge_geo_out = n_merge.outputs.get("Geometry") or n_merge.outputs[0]

    links.new(in_geo, merge_geo_in)
    links.new(merge_geo_out, out_geo)

    return group

def get_input_identifier(node_group, input_name):
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
    """Setup Geometry LOD Modifiers"""
    bl_idname = "tot.geo_lod_setup"
    bl_label = "Setup Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        method = scn.geo_lod_method
        min_faces = scn.geo_lod_min_faces
        
        created = 0
        try:
            lod_group = ensure_lod_node_group() if method == 'GNODES' else None
        except Exception as e:
            self.report({'ERROR'}, f"Create Node Error: {e}")
            return {'CANCELLED'}
        
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue
            if min_faces > 0 and len(obj.data.polygons) < min_faces: continue
            
            if method == 'DECIMATE':
                if obj.modifiers.get(GEO_NODES_MOD_NAME):
                    obj.modifiers.remove(obj.modifiers.get(GEO_NODES_MOD_NAME))
                mod = obj.modifiers.get(DECIMATE_MOD_NAME)
                if not mod:
                    mod = obj.modifiers.new(DECIMATE_MOD_NAME, 'DECIMATE')
                    mod.decimate_type = 'COLLAPSE'
                    mod.ratio = 1.0
                    obj["_tot_geo_lod_created"] = True
                    created += 1
                    
            elif method == 'GNODES':
                if obj.modifiers.get(DECIMATE_MOD_NAME):
                    obj.modifiers.remove(obj.modifiers.get(DECIMATE_MOD_NAME))

                mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
                force_rebuild = False
                if mod and mod.node_group and mod.node_group.name != "TOT_GEO_LOD_Advanced":
                    force_rebuild = True
                if mod and len(mod.node_group.interface.items_tree) != len(lod_group.interface.items_tree):
                    force_rebuild = True

                if not mod or force_rebuild:
                    if mod: obj.modifiers.remove(mod)
                    mod = obj.modifiers.new(name=GEO_NODES_MOD_NAME, type='NODES')
                    mod.node_group = lod_group
                    obj["_tot_geo_lod_created"] = True
                    created += 1
                
                gn_id_angle = get_input_identifier(lod_group, GN_INPUT_ANGLE)
                if gn_id_angle:
                    mod[gn_id_angle] = scn.geo_lod_angle_threshold

        self.report({'INFO'}, f"Setup complete: {created} modifiers updated.")
        return {'FINISHED'}

class TOT_OT_GeoLODUpdateAsync(bpy.types.Operator):
    """
    异步计算屏幕占比并更新 LOD 修改器
    """
    bl_idname = "tot.geo_lod_update_async"
    bl_label = "Update Geometry (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []
    _total_tasks = 0
    _processed = 0
    _updated_count = 0
    TIME_BUDGET = 0.05   #帧时间

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
        
        self._queue = []
        for obj in context.scene.objects:
            if obj.type == 'MESH' and not obj.hide_viewport:
                if obj.modifiers.get(target_mod):
                    self._queue.append(obj)
        
        if not self._queue:
            self.report({'WARNING'}, "Run 'Setup' first.")
            return {'CANCELLED'}

        self._total_tasks = len(self._queue)
        self._processed = 0
        self._updated_count = 0
        self.method = method
        self.min_protection = scn.geo_lod_min_ratio
        
        self.angle_threshold = scn.geo_lod_angle_threshold
        
        self.gn_id_factor = None
        self.gn_id_angle = None
        
        if method == 'GNODES':
            group = bpy.data.node_groups.get("TOT_GEO_LOD_Advanced")
            self.gn_id_factor = get_input_identifier(group, GN_INPUT_FACTOR)
            self.gn_id_angle = get_input_identifier(group, GN_INPUT_ANGLE)

        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window) 
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def process_object(self, context, obj):
        # 1. 计算 Ratio (略，调用 utils)
        if hasattr(utils, 'get_normalized_screen_ratio'):
            raw_ratio = utils.get_normalized_screen_ratio(context.scene, obj, self.cam)
        else:
            raw_ratio = 0.5 
        
        # 2. Stepping
        if hasattr(utils, 'get_stepped_lod_factor'):
            target_factor = utils.get_stepped_lod_factor(raw_ratio, self.min_protection)
        else:
            target_factor = 1.0

        # 3. Apply
        if self.method == 'DECIMATE':
            mod = obj.modifiers.get(DECIMATE_MOD_NAME)
            if mod and abs(mod.ratio - target_factor) > 0.05:
                mod.ratio = target_factor
                obj.update_tag() # [修复1] 强制通知 Blender 这个物体数据变了
                self._updated_count += 1
                    
        elif self.method == 'GNODES':
            mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
            if mod:
                # 标记是否有变化
                changed = False
                
                # 更新强度 (LOD_Factor)
                if self.gn_id_factor:
                    try:
                        curr = mod.get(self.gn_id_factor, 1.0)
                        if abs(curr - target_factor) > 0.05:
                            mod[self.gn_id_factor] = target_factor
                            changed = True
                    except: pass
                
                # 更新角度阈值 (Angle_Threshold)
                if self.gn_id_angle:
                    try:
                        # 检查当前值，避免重复写入
                        curr_angle = mod.get(self.gn_id_angle, 1.5)
                        if abs(curr_angle - self.angle_threshold) > 0.01:
                            mod[self.gn_id_angle] = self.angle_threshold
                            changed = True
                    except: pass
                
                # [修复1] 只有数值真正改变时，才强制刷新物体
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