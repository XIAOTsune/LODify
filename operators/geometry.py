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
def ensure_lod_node_group():
    """
    创建/更新 LOD 节点组 (Geometry Nodes)
    功能：
    1. 接收 LOD_Factor (0.0~1.0) 和 Angle_Threshold
    2. 接收 Max_Merge_Dist (最大合并距离)
    3. 根据 Factor 动态计算合并距离：离得越远(Factor越小)，合并半径越大
    4. 保护锐利边缘，只合并平坦区域
    """
    name = "TOT_GEO_LOD_Advanced" 
    group = bpy.data.node_groups.get(name)
    
    if not group:
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    
    # -----------------------------------------------------------
    # 内嵌辅助函数：安全创建节点
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

    # ===========================================================
    # 1. 定义接口 (Interface) - 确保输入输出端口存在
    # ===========================================================
    if hasattr(group, "interface"):
        # 注意：这里我们只在初始化或不匹配时清理，或者简单地追加
        # 为了代码简洁，这里假设每次重建接口，实际生产中可优化
        group.interface.clear()
        
        # [0] Geometry In
        group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        
        # [1] LOD_Factor (0.0 = 远/低模, 1.0 = 近/高模)
        s1 = group.interface.new_socket(name=GN_INPUT_FACTOR, in_out='INPUT', socket_type='NodeSocketFloat')
        s1.min_value = 0.0
        s1.max_value = 1.0
        s1.default_value = 1.0
        
        # [2] Angle_Threshold (弧度，用于保护边缘)
        s2 = group.interface.new_socket(name=GN_INPUT_ANGLE, in_out='INPUT', socket_type='NodeSocketFloat')
        s2.min_value = 0.0
        s2.max_value = 3.14159
        s2.default_value = 1.5 
        
        # [3] Max_Merge_Dist (新参数：最远处的合并半径)
        # 即使你在外部没定义常量 GN_INPUT_MAX_DIST，这里用字符串也行
        dist_name = "Max_Merge_Dist" 
        if "GN_INPUT_MAX_DIST" in globals(): dist_name = GN_INPUT_MAX_DIST
            
        s3 = group.interface.new_socket(name=dist_name, in_out='INPUT', socket_type='NodeSocketFloat')
        s3.min_value = 0.0
        s3.default_value = 0.5 # 默认最大合并 0.5m
        
        # [0] Geometry Out
        group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = group.nodes
    links = group.links
    nodes.clear()

    # ===========================================================
    # 2. 创建节点
    # ===========================================================
    
    # 输入输出节点
    n_in = nodes.new("NodeGroupInput")
    n_in.location = (-900, 0)
    
    n_out = nodes.new("NodeGroupOutput")
    n_out.location = (600, 0)

    # [Merge By Distance] - 核心减面节点
    n_merge = safe_create_node(
        nodes, 
        ["GeometryNodeMergeByDistance", "GeometryNodeMeshMergeByDistance"], 
        label="Merge by Distance"
    )
    if not n_merge: raise RuntimeError("Missing Merge Node")
    n_merge.location = (300, 0)
    
    # [Map Range] - 动态距离控制核心
    # 逻辑：将 LOD_Factor (0~1) 映射为 Distance (Max~Min)
    # 当 Factor=1 (近景) -> Distance=0 (不合并)
    # 当 Factor=0 (远景) -> Distance=Max_Merge_Dist (强合并)
    n_map_dist = nodes.new("ShaderNodeMapRange") 
    n_map_dist.label = "Dynamic Distance"
    n_map_dist.location = (50, -250)
    
    n_map_dist.inputs['From Min'].default_value = 0.0   # Factor 0 (远)
    n_map_dist.inputs['From Max'].default_value = 1.0   # Factor 1 (近)
    # To Min 将由外部输入的 Max_Dist 控制
    n_map_dist.inputs['To Max'].default_value = 0.0001  # 近处几乎不合并

    # [Edge Angle] - 边缘检测
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

    # ===========================================================
    # 3. 连线逻辑
    # ===========================================================

    if n_edge_angle:
        # --- 如果版本支持 Edge Angle (高级模式) ---
        n_edge_angle.location = (-600, 250)

        # [Compare] Is Flat? (判断当前边是否平坦)
        n_is_flat = nodes.new("FunctionNodeCompare")
        n_is_flat.data_type = 'FLOAT'
        n_is_flat.operation = 'LESS_THAN'
        n_is_flat.label = "Is Flat?"
        n_is_flat.location = (-350, 250)

        # [Math] 1.0 - LOD (反转 Factor 用于随机概率)
        n_invert = nodes.new("ShaderNodeMath")
        n_invert.operation = 'SUBTRACT'
        n_invert.label = "1.0 - LOD"
        n_invert.inputs[0].default_value = 1.0
        n_invert.location = (-600, -150)

        # [Random] 随机筛选点
        n_random = nodes.new("FunctionNodeRandomValue")
        n_random.data_type = 'BOOLEAN'
        n_random.label = "Random Cull"
        n_random.location = (-350, -150)

        # [Boolean And] 综合条件：既要平坦，又要命中随机概率
        n_and = nodes.new("FunctionNodeBooleanMath")
        n_and.operation = 'AND'
        n_and.label = "Filter"
        n_and.location = (-100, 100)

        # --- 连线 A: 选点逻辑 (Selection) ---
        # 1. 边缘角度 < 阈值 ?
        links.new(n_edge_angle.outputs[0], n_is_flat.inputs[0])
        links.new(n_in.outputs[2], n_is_flat.inputs[1]) # Input[2] is Angle_Threshold

        # 2. 随机概率 = 1 - LOD
        links.new(n_in.outputs[1], n_invert.inputs[1])  # Input[1] is LOD_Factor
        links.new(n_invert.outputs[0], n_random.inputs["Probability"])

        # 3. 组合条件
        links.new(n_is_flat.outputs[0], n_and.inputs[0])
        links.new(n_random.outputs[3], n_and.inputs[1]) # Random Boolean Output is index 3

        # 4. 连入 Merge Selection
        try:
            target_socket = n_merge.inputs.get("Selection") or n_merge.inputs[1]
            links.new(n_and.outputs[0], target_socket)
        except: pass

        # --- 连线 B: 动态距离逻辑 (Distance) ---
        # 1. Input[1] (Factor) -> Map Range Value
        links.new(n_in.outputs[1], n_map_dist.inputs['Value'])
        
        # 2. Input[3] (Max_Dist) -> Map Range 'To Min' (对应 Factor 0 也就是最远处的距离)
        # 注意：这里假设输入顺序是 [Geo, Factor, Angle, MaxDist] -> Index 3
        links.new(n_in.outputs[3], n_map_dist.inputs['To Min'])
        
        # 3. Map Range Result -> Merge Distance
        links.new(n_map_dist.outputs['Result'], n_merge.inputs['Distance'])

    else:
        # --- 降级模式 (Fallback) ---
        # 注意缩进：这里的 else 是对应最外层的 if n_edge_angle
        print("[TOT] No Edge Angle node found. Fallback mode.")
        
        # 即使在降级模式，我们也尝试连接动态距离，这样至少能在不考虑边缘的情况下大幅减面
        try:
             # Input[1] Factor -> Map Range
             links.new(n_in.outputs[1], n_map_dist.inputs['Value'])
             # Input[3] MaxDist -> Map Range To Min
             links.new(n_in.outputs[3], n_map_dist.inputs['To Min'])
             # Map Range -> Merge Distance
             links.new(n_map_dist.outputs['Result'], n_merge.inputs['Distance'])
        except:
             pass
             
        # 只有几何流连接，不连接 Selection（全选）
        links.new(n_in.outputs[0], n_merge.inputs[0]) 

    # ===========================================================
    # 4. 主几何流连线 (Common)
    # ===========================================================
    in_geo = n_in.outputs[0]
    out_geo = n_out.inputs[0]
    merge_geo_in = n_merge.inputs.get("Geometry") or n_merge.inputs[0]
    merge_geo_out = n_merge.outputs.get("Geometry") or n_merge.outputs[0]

    # 注意：如果上面连了，这里重复连没关系，Blender 会覆盖
    # 但在高级模式下，Selection 已经筛选了点，这里只需连 Geometry
    if not n_edge_angle:
        # 降级模式下直接连
        pass 
    
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
                
                gn_id_dist = get_input_identifier(lod_group, GN_INPUT_MAX_DIST)
                if gn_id_dist:
                     mod[gn_id_dist] = scn.geo_lod_max_dist # 从面板读取值

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
        
        # --- 获取最新的全局参数 ---
        self.min_protection = scn.geo_lod_min_ratio
        self.min_faces = scn.geo_lod_min_faces
        self.angle_threshold = scn.geo_lod_angle_threshold
        self.max_dist = scn.geo_lod_max_dist
        
        self.gn_id_factor = None
        self.gn_id_angle = None
        self.gn_id_dist = None
        
        if method == 'GNODES':
            group = bpy.data.node_groups.get("TOT_GEO_LOD_Advanced")
            # [修复点] 这里直接调用当前文件定义的函数，不需要 utils. 前缀
            self.gn_id_factor = get_input_identifier(group, GN_INPUT_FACTOR)
            self.gn_id_angle = get_input_identifier(group, GN_INPUT_ANGLE)
            # 尝试获取 Max_Merge_Dist 的接口 ID
            self.gn_id_dist = get_input_identifier(group, GN_INPUT_MAX_DIST)

        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window) 
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def process_object(self, context, obj):
        """
        处理单个物体的 LOD 更新逻辑：
        1. 检查面数保护 (Min Faces) -> 如果受保护，强制 Factor=1.0
        2. 计算屏幕占比 (Screen Ratio)
        3. 写入修改器 (Decimate 或 GN)
        """
        
        # ===========================================================
        # 1. 面数保护检查 (Min Faces Protection)
        # ===========================================================
        # 逻辑：如果当前物体面数 < 设置的最小面数，强制不减面 (target_factor = 1.0)
        # 这让用户在面板调整 Min Faces 后点击更新，能立即“救回”那些被误杀的小物体
        is_protected_by_faces = False
        if hasattr(obj.data, "polygons"):
            # 注意：对于面数极多的物体，len() 可能会微耗时，但在异步 Modal 里通常可接受
            if len(obj.data.polygons) < self.min_faces:
                is_protected_by_faces = True

        # ===========================================================
        # 2. 计算目标强度 (Target Factor)
        # ===========================================================
        if is_protected_by_faces:
            # 如果触发面数保护，直接设为 1.0 (保留原样)
            target_factor = 1.0
        else:
            # 否则，正常进行屏幕占比计算
            if hasattr(utils, 'get_normalized_screen_ratio'):
                raw_ratio = utils.get_normalized_screen_ratio(context.scene, obj, self.cam)
            else:
                raw_ratio = 0.5 
            
            if hasattr(utils, 'get_stepped_lod_factor'):
                target_factor = utils.get_stepped_lod_factor(raw_ratio, self.min_protection)
            else:
                target_factor = 1.0

        # ===========================================================
        # 3. 应用到修改器 (Apply Modifiers)
        # ===========================================================
        
        # 定义极小的容差值 (Epsilon)，保证微调参数能立即生效
        EPSILON_FACTOR = 0.001 
        EPSILON_ANGLE = 0.001   
        EPSILON_DIST = 0.0001   

        # --- 模式 A: 传统减面修改器 (Decimate) ---
        if self.method == 'DECIMATE':
            mod = obj.modifiers.get(DECIMATE_MOD_NAME)
            if mod:
                # 如果受面数保护，Ratio 恢复为 1.0；否则应用计算出的 Ratio
                if abs(mod.ratio - target_factor) > EPSILON_FACTOR:
                    mod.ratio = target_factor
                    obj.update_tag() 
                    self._updated_count += 1
            
        # --- 模式 B: 几何节点 (Geometry Nodes) ---
        elif self.method == 'GNODES':
            mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
            if mod:
                changed = False
                
                # 3.1 更新强度 (LOD_Factor)
                if self.gn_id_factor:
                    try:
                        curr = mod.get(self.gn_id_factor, 1.0)
                        if abs(curr - target_factor) > EPSILON_FACTOR:
                            mod[self.gn_id_factor] = target_factor
                            changed = True
                    except: pass
                
                # 3.2 更新角度阈值 (Angle_Threshold)
                if self.gn_id_angle:
                    try:
                        curr_angle = mod.get(self.gn_id_angle, 1.5)
                        # 检查当前值与全局设置的差异
                        if abs(curr_angle - self.angle_threshold) > EPSILON_ANGLE:
                            mod[self.gn_id_angle] = self.angle_threshold
                            changed = True
                    except: pass

                # 3.3 更新最大合并距离 (Max_Merge_Dist)
                if hasattr(self, 'gn_id_dist') and self.gn_id_dist:
                    try:
                        curr_dist = mod.get(self.gn_id_dist, 0.5)
                        target_dist = getattr(self, 'max_dist', 0.5) 
                        
                        if abs(curr_dist - target_dist) > EPSILON_DIST:
                            mod[self.gn_id_dist] = target_dist
                            changed = True
                    except: pass
                
                # 4. 提交更改
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