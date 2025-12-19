import bpy
import time
from mathutils import Vector
import traceback

# 常量定义
POM_NODE_GROUP_NAME = "TOT_POM_Calculator"
POM_NODE_NAME = "TOT_POM_Node"

# =============================================================================
# 核心工具：跨语言接口查找
# =============================================================================
def get_socket_by_id(node, english_ids):
    """
    通过内部 Identifier 查找接口 (无视 Blender 界面语言)
    english_ids: 可以是单个字符串，也可以是列表 (例如 ['Base Color', 'BaseColor'])
    """
    if isinstance(english_ids, str):
        english_ids = [english_ids]
        
    for socket in node.inputs:
        # Blender 4.0/5.0+ 内部 ID 通常是英文
        if socket.identifier in english_ids:
            return socket
        # 兼容旧版本或特殊情况，检查 name (作为后备)
        if socket.name in english_ids:
            return socket
            
    return None

def find_image_source_recursive(node, depth=0, max_depth=6):
    """
    递归回溯，寻找源头图片节点。
    """
    if not node or depth > max_depth: return None, None

    if node.type == 'TEX_IMAGE':
        return node, node.outputs[0]

    # 支持穿透的节点类型
    pass_through_types = {
        'DISPLACEMENT', 'MATH', 'VECTOR_MATH', 'MIX_RGB', 'MIX_SHADER', 
        'CURVE_RGB', 'VALTORGB', 'INVERT', 'MAPPING', 'NORMAL_MAP', 'BUMP'
    }
    
    if node.type in pass_through_types:
        # 遍历该节点所有连了线的输入，继续往上找
        for input_socket in node.inputs:
            if input_socket.is_linked:
                link = input_socket.links[0]
                found_node, found_socket = find_image_source_recursive(link.from_node, depth + 1, max_depth)
                if found_node:
                    return found_node, found_socket
    
    return None, None

# =============================================================================
# 节点组构建
# =============================================================================
def ensure_pom_node_group():
    group = bpy.data.node_groups.get(POM_NODE_GROUP_NAME)
    if not group:
        group = bpy.data.node_groups.new(name=POM_NODE_GROUP_NAME, type="ShaderNodeTree")
    
    # Blender 4.0+ / 5.0 使用 interface API
    if hasattr(group, "interface"):
        group.interface.clear()
        group.interface.new_socket(name="Vector", in_out='INPUT', socket_type='NodeSocketVector')
        group.interface.new_socket(name="Height", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Depth Scale", in_out='INPUT', socket_type='NodeSocketFloat')
        group.interface.new_socket(name="Result Vector", in_out='OUTPUT', socket_type='NodeSocketVector')
    
    _build_pom_nodes(group)
    return group

def _build_pom_nodes(group):
    nodes = group.nodes
    links = group.links
    nodes.clear()
    
    # 简易视差算法节点图
    n_in = nodes.new("NodeGroupInput"); n_in.location = (-800, 0)
    n_out = nodes.new("NodeGroupOutput"); n_out.location = (400, 0)
    
    n_geo = nodes.new("ShaderNodeNewGeometry"); n_geo.location = (-800, 200)
    n_transform = nodes.new("ShaderNodeVectorTransform")
    n_transform.convert_from = 'WORLD'; n_transform.convert_to = 'OBJECT'; n_transform.location = (-600, 200)
    
    n_sep = nodes.new("ShaderNodeSeparateXYZ"); n_sep.location = (-400, 200)
    
    n_sub = nodes.new("ShaderNodeMath")
    n_sub.operation = 'SUBTRACT'; n_sub.inputs[1].default_value = 1.0; n_sub.location = (-400, 0)
    
    n_mult_scale = nodes.new("ShaderNodeMath")
    n_mult_scale.operation = 'MULTIPLY'; n_mult_scale.location = (-200, 0)
    
    n_vec_mult = nodes.new("ShaderNodeVectorMath")
    n_vec_mult.operation = 'MULTIPLY'; n_vec_mult.location = (0, 100)
    
    n_vec_add = nodes.new("ShaderNodeVectorMath")
    n_vec_add.operation = 'ADD'; n_vec_add.location = (200, 0)
    
    n_combine = nodes.new("ShaderNodeCombineXYZ"); n_combine.location = (-200, 200)
    
    # Links
    links.new(n_geo.outputs['Incoming'], n_transform.inputs[0])
    links.new(n_transform.outputs[0], n_sep.inputs[0])
    links.new(n_sep.outputs['X'], n_combine.inputs['X'])
    links.new(n_sep.outputs['Y'], n_combine.inputs['Y'])
    links.new(n_in.outputs['Height'], n_sub.inputs[0])
    links.new(n_sub.outputs[0], n_mult_scale.inputs[0])
    links.new(n_in.outputs['Depth Scale'], n_mult_scale.inputs[1])
    links.new(n_combine.outputs[0], n_vec_mult.inputs[0])
    links.new(n_mult_scale.outputs[0], n_vec_mult.inputs[1])
    links.new(n_in.outputs['Vector'], n_vec_add.inputs[0])
    links.new(n_vec_mult.outputs[0], n_vec_add.inputs[1])
    links.new(n_vec_add.outputs[0], n_out.inputs[0])

# =============================================================================
# Debug Operator (排查工具)
# =============================================================================
class TOT_OT_POMDebug(bpy.types.Operator):
    """排查当前选中物体的材质接口 (Debug Mode)"""
    bl_idname = "tot.pom_debug"
    bl_label = "Debug POM"
    
    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a Mesh first.")
            return {'CANCELLED'}
            
        print(f"\n[TOT DEBUG] Analyzing {obj.name}...")
        found = False
        
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes: continue
            print(f"  Material: {mat.name}")
            
            # 1. Check Output -> Displacement
            out_node = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
            if out_node:
                # 使用 ID 'Displacement' 查找
                disp_sock = get_socket_by_id(out_node, 'Displacement')
                if disp_sock:
                    print(f"    [OK] Found Output 'Displacement' socket (Linked: {disp_sock.is_linked})")
                    if disp_sock.is_linked:
                        img, _ = find_image_source_recursive(disp_sock.links[0].from_node)
                        if img: 
                            print(f"    [SUCCESS] Traced to Image: {img.name}")
                            found = True
                else:
                    print("    [FAIL] Output node has no 'Displacement' identifier socket.")

            # 2. Check BSDF -> Base Color
            if not found:
                bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bsdf:
                    # 使用 ID 'Base Color' 查找
                    bc_sock = get_socket_by_id(bsdf, ['Base Color', 'BaseColor'])
                    if bc_sock:
                        print(f"    [OK] Found BSDF 'Base Color' socket (Linked: {bc_sock.is_linked})")
                        if bc_sock.is_linked:
                            img, _ = find_image_source_recursive(bc_sock.links[0].from_node)
                            if img:
                                print(f"    [SUCCESS] Traced to Fallback Image: {img.name}")
                                found = True
        
        if found:
            self.report({'INFO'}, "Debug: Valid texture found! Try Update now.")
        else:
            self.report({'WARNING'}, "Debug: No valid texture found. Check System Console.")
            
        return {'FINISHED'}

# =============================================================================
# Main Operator
# =============================================================================
class TOT_OT_POMUpdateAsync(bpy.types.Operator):
    """异步应用 POM (修复中文版兼容性)"""
    bl_idname = "tot.pom_update_async"
    bl_label = "Update POM (Async)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _queue = []
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
                except Exception as e:
                    print(f"POM Error on {obj.name}:")
                    traceback.print_exc()
                self._processed += 1
                if (time.time() - start_time) > self.TIME_BUDGET: break
            context.window_manager.progress_update(self._processed)
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        scn = context.scene.tot_props
        if not scn.exp_pom_enabled: scn.exp_pom_enabled = True
        self.pom_group = ensure_pom_node_group()
        self.target_depth = scn.exp_pom_depth
        
        self._queue = []
        # 优先处理选中物体
        candidates = context.selected_objects if context.selected_objects else context.scene.objects
        for obj in candidates:
            if obj.type == 'MESH' and not obj.hide_viewport and obj.material_slots:
                self._queue.append(obj)

        if not self._queue:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        self._total_tasks = len(self._queue)
        self._processed = 0
        self._updated_count = 0
        context.window_manager.progress_begin(0, self._total_tasks)
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def process_object(self, context, obj):
        modified = False
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes: continue
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            # 1. 检查是否存在 POM
            pom_node = next((n for n in nodes if n.name == POM_NODE_NAME), None)
            if pom_node:
                if abs(pom_node.inputs['Depth Scale'].default_value - self.target_depth) > 0.001:
                    pom_node.inputs['Depth Scale'].default_value = self.target_depth
                    modified = True
                continue 

            # 2. 寻找高度源 (使用 ID 查找)
            height_node, height_socket = None, None
            
            # A. Output -> Displacement
            out_node = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
            if out_node:
                disp_sock = get_socket_by_id(out_node, 'Displacement')
                if disp_sock and disp_sock.is_linked:
                    height_node, height_socket = find_image_source_recursive(disp_sock.links[0].from_node)

            # B. BSDF -> Base Color
            if not height_node:
                bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bsdf:
                    bc_sock = get_socket_by_id(bsdf, ['Base Color', 'BaseColor']) # 兼容不同版本 ID
                    if bc_sock and bc_sock.is_linked:
                        height_node, height_socket = find_image_source_recursive(bc_sock.links[0].from_node)

            if not height_node: continue

            # 3. 创建 POM 节点
            pom_node = nodes.new("ShaderNodeGroup")
            pom_node.name = POM_NODE_NAME
            pom_node.label = "TOT Parallax"
            pom_node.node_group = self.pom_group
            pom_node.location = (height_node.location.x - 300, height_node.location.y)
            pom_node.inputs['Depth Scale'].default_value = self.target_depth
            
            links.new(height_socket, pom_node.inputs['Height'])
            
            # 4. 连入 UV (Image Texture 的 Vector 接口 ID 也是 'Vector')
            uv_sock = get_socket_by_id(height_node, 'Vector')
            if uv_sock and uv_sock.is_linked:
                links.new(uv_sock.links[0].from_socket, pom_node.inputs['Vector'])
            else:
                uv_map = nodes.new("ShaderNodeUVMap")
                uv_map.location = (pom_node.location.x - 300, pom_node.location.y)
                links.new(uv_map.outputs[0], pom_node.inputs['Vector'])
            
            # 5. 劫持其他图片 (遍历所有 Texture 节点)
            for n in nodes:
                if n.type == 'TEX_IMAGE' and n != height_node:
                    vec_sock = get_socket_by_id(n, 'Vector')
                    if vec_sock:
                        links.new(pom_node.outputs['Result Vector'], vec_sock)
            
            modified = True
            
        if modified: self._updated_count += 1

    def finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        for area in context.screen.areas: area.tag_redraw()
        if self._updated_count > 0:
            self.report({'INFO'}, f"POM Setup: {self._updated_count} objects.")
        else:
            self.report({'WARNING'}, "POM: No valid materials found.")
        return {'FINISHED'}

class TOT_OT_POMReset(bpy.types.Operator):
    bl_idname = "tot.pom_reset"
    bl_label = "Reset POM"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        count = 0
        candidates = context.selected_objects if context.selected_objects else context.scene.objects
        for obj in candidates:
            if obj.type != 'MESH': continue
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes: continue
                
                pom_node = next((n for n in mat.node_tree.nodes if n.name == POM_NODE_NAME), None)
                if pom_node:
                    orig_uv = None
                    if len(pom_node.inputs) > 0 and pom_node.inputs[0].is_linked:
                        orig_uv = pom_node.inputs[0].links[0].from_socket
                    
                    if len(pom_node.outputs) > 0 and pom_node.outputs[0].is_linked:
                         for link in list(pom_node.outputs[0].links):
                             if orig_uv: mat.node_tree.links.new(orig_uv, link.to_socket)
                             else: mat.node_tree.links.remove(link)
                    mat.node_tree.nodes.remove(pom_node)
                    count += 1
        self.report({'INFO'}, f"Reset {count} materials.")
        return {'FINISHED'}

classes = (TOT_OT_POMDebug, TOT_OT_POMUpdateAsync, TOT_OT_POMReset)
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)