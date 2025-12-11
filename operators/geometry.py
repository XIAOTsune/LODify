import bpy
from mathutils import Vector

# 定义常量
DECIMATE_MOD_NAME = "TOT_LOD_DECIMATE"
GEO_NODES_MOD_NAME = "TOT_GEO_LOD"
GN_INPUT_NAME = "LOD_Factor" # 几何节点中定义的输入名称

# --- Helper: 节点组逻辑 ---
def ensure_lod_node_group():
    """确保存在一个几何 LOD 节点组"""
    name = "TOT_GEO_LOD_Basic"
    group = bpy.data.node_groups.get(name)
    if not group:
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
        
        # 兼容 Blender 4.0+ / 5.0 接口
        if hasattr(group, "interface"):
            group.interface.clear()
            group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            # 这里的 name="LOD_Factor" 很重要
            sock_factor = group.interface.new_socket(name=GN_INPUT_NAME, in_out='INPUT', socket_type='NodeSocketFloat')
            sock_factor.min_value = 0.0
            sock_factor.max_value = 1.0
            sock_factor.default_value = 0.0
            group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
        nodes = group.nodes
        links = group.links
        nodes.clear()
        
        # --- 节点构建 ---
        input_node = nodes.new("NodeGroupInput")
        output_node = nodes.new("NodeGroupOutput")
        input_node.location = (-400, 0)
        output_node.location = (400, 0)
        
        # 1. BBox 对角线计算
        node_bbox = nodes.new("GeometryNodeBoundBox")
        node_bbox.location = (-200, 200)
        
        node_sub = nodes.new("ShaderNodeVectorMath")
        node_sub.operation = 'SUBTRACT'
        node_sub.location = (0, 200)
        
        node_len = nodes.new("ShaderNodeVectorMath")
        node_len.operation = 'LENGTH'
        node_len.location = (160, 200)
        
        # 2. 基准距离 (0.1 系数)
        node_math_base = nodes.new("ShaderNodeMath")
        node_math_base.operation = 'MULTIPLY'
        node_math_base.inputs[1].default_value = 0.1
        node_math_base.location = (320, 200)
        
        # 3. 核心控制：乘以 LOD_Factor
        node_math_final = nodes.new("ShaderNodeMath")
        node_math_final.operation = 'MULTIPLY'
        node_math_final.label = "Strength Control"
        node_math_final.location = (320, 0)
        
        # 4. Merge Node
        node_merge = nodes.new("GeometryNodeMergeByDistance")
        node_merge.location = (500, 0)
        
        # --- 连线 ---
        links.new(input_node.outputs["Geometry"], node_merge.inputs["Geometry"])
        links.new(input_node.outputs["Geometry"], node_bbox.inputs["Geometry"])
        
        links.new(node_bbox.outputs["Min"], node_sub.inputs[0])
        links.new(node_bbox.outputs["Max"], node_sub.inputs[1])
        links.new(node_sub.outputs["Vector"], node_len.inputs["Vector"])
        links.new(node_len.outputs["Value"], node_math_base.inputs[0])
        
        links.new(node_math_base.outputs["Value"], node_math_final.inputs[0])
        
        # 连接接口输入 (LOD_Factor) 到 Math Node
        # 注意：使用 Identifier 查找或者索引查找，这里用 Interface 对应的 output
        # 在 Group Input 节点上，outputs 的顺序对应 Interface 定义的 Inputs
        # 0: Geometry, 1: LOD_Factor
        links.new(input_node.outputs[1], node_math_final.inputs[1])
        
        links.new(node_math_final.outputs["Value"], node_merge.inputs["Distance"])
        links.new(node_merge.outputs["Geometry"], output_node.inputs["Geometry"])

    return group

def get_input_identifier(node_group, input_name):
    """
    [核心修复] 获取几何节点输入属性的真实 Identifier
    Blender 内部并不总是使用 Name 作为 Key，而是使用 Identifier (如 "Socket_2")
    """
    if not node_group:
        return None
        
    # Blender 4.0+ 使用 interface
    if hasattr(node_group, "interface"):
        for item in node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if item.name == input_name:
                    return item.identifier
    # 旧版本兼容
    elif hasattr(node_group, "inputs"):
        for input_socket in node_group.inputs:
            if input_socket.name == input_name:
                return input_socket.identifier
                
    return None

# --- Operators ---

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
        lod_group = ensure_lod_node_group() if method == 'GNODES' else None
        
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue
            if min_faces > 0 and len(obj.data.polygons) < min_faces: continue
            
            if method == 'DECIMATE':
                # 清理 GN
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
                # 清理 Decimate
                if obj.modifiers.get(DECIMATE_MOD_NAME):
                    obj.modifiers.remove(obj.modifiers.get(DECIMATE_MOD_NAME))

                mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
                if not mod:
                    mod = obj.modifiers.new(name=GEO_NODES_MOD_NAME, type='NODES')
                    mod.node_group = lod_group
                    obj["_tot_geo_lod_created"] = True
                    created += 1

        self.report({'INFO'}, f"Setup complete: {created} modifiers added.")
        return {'FINISHED'}

class TOT_OT_GeoLODUpdate(bpy.types.Operator):
    """Update Geometry based on Camera Distance"""
    bl_idname = "tot.geo_lod_update"
    bl_label = "Update Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        if not scn.geo_lod_enabled:
            self.report({'WARNING'}, "Geometry LOD is disabled.")
            return {'CANCELLED'}
        
        cam = scn.lod_camera or context.scene.camera
        if not cam: 
            self.report({'ERROR'}, "No Camera found.")
            return {'CANCELLED'}
        
        cam_loc = cam.matrix_world.translation
        d0, d1, d2 = scn.lod_dist_0, scn.lod_dist_1, scn.lod_dist_2
        method = scn.geo_lod_method
        strength = scn.geo_lod_min_ratio 
        
        updated = 0
        
        gn_identifier = None
        if method == 'GNODES':
            group = bpy.data.node_groups.get("TOT_GEO_LOD_Basic")
            gn_identifier = get_input_identifier(group, GN_INPUT_NAME)
            if not gn_identifier:
                ensure_lod_node_group()
                group = bpy.data.node_groups.get("TOT_GEO_LOD_Basic")
                gn_identifier = get_input_identifier(group, GN_INPUT_NAME)
        
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue
            
            try:
                bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                center = sum(bbox_world, Vector()) / 8.0
            except:
                center = obj.matrix_world.translation
            
            dist = (center - cam_loc).length
            
            if dist <= d0: level = 0
            elif dist <= d1: level = 1
            elif dist <= d2: level = 2
            else: level = 3
            
            factor = level / 3.0
            
            if method == 'DECIMATE':
                mod = obj.modifiers.get(DECIMATE_MOD_NAME)
                if mod:
                    target_ratio = 1.0 - factor * (1.0 - strength)
                    if mod.ratio != target_ratio:
                        mod.ratio = target_ratio
                        # [核心修复 1] 标记物体需要更新
                        obj.update_tag()
                        updated += 1
            
            elif method == 'GNODES':
                mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
                if mod and gn_identifier:
                    final_value = factor * strength
                    try:
                        # 仅当值确实改变时才更新，节省性能
                        if mod[gn_identifier] != final_value:
                            mod[gn_identifier] = final_value
                            # [核心修复 2] 标记物体数据层需要更新
                            # refresh={'DATA'} 告诉 Blender 几何数据变了
                            obj.update_tag(refresh={'DATA'})
                            updated += 1
                    except Exception as e:
                        pass
        
        #  强制视口刷新
        # 这确保了在一帧内所有的 update_tag 都能被立即渲染出来
        context.view_layer.update()

        self.report({'INFO'}, f"Updated {updated} objects (Strength: {strength:.2f}).")
        return {'FINISHED'}

class TOT_OT_GeoLODReset(bpy.types.Operator):
    """Reset / Remove Modifiers"""
    bl_idname = "tot.geo_lod_reset"
    bl_label = "Reset Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed = 0
        for obj in context.scene.objects:
            mod_dec = obj.modifiers.get(DECIMATE_MOD_NAME)
            if mod_dec: 
                obj.modifiers.remove(mod_dec)
                removed += 1
                
            mod_gn = obj.modifiers.get(GEO_NODES_MOD_NAME)
            if mod_gn: 
                obj.modifiers.remove(mod_gn)
                removed += 1
            
            if "_tot_geo_lod_created" in obj:
                del obj["_tot_geo_lod_created"]

        self.report({'INFO'}, f"Reset complete. Cleaned {removed} objects.")
        return {'FINISHED'}

class TOT_OT_GeoLODApply(bpy.types.Operator):
    """Apply LOD Modifier"""
    bl_idname = "tot.geo_lod_apply"
    bl_label = "Apply (Destructive)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        method = scn.geo_lod_method
        target_mod_name = DECIMATE_MOD_NAME if method == 'DECIMATE' else GEO_NODES_MOD_NAME
        
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        applied = 0
        targets = [o for o in context.scene.objects if o.type == 'MESH' and o.modifiers.get(target_mod_name)]
        
        if not targets:
            self.report({'WARNING'}, "No modifiers found to apply.")
            return {'CANCELLED'}

        active_old = context.view_layer.objects.active
        selected_old = context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in targets:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            try:
                bpy.ops.object.modifier_apply(modifier=target_mod_name)
                if "_tot_geo_lod_created" in obj:
                    del obj["_tot_geo_lod_created"]
                applied += 1
            except Exception as e:
                print(f"Apply failed on {obj.name}: {e}")
            obj.select_set(False)
            
        for o in selected_old:
            try: o.select_set(True)
            except: pass
        if active_old:
            context.view_layer.objects.active = active_old
            
        self.report({'INFO'}, f"Applied LOD to {applied} objects.")
        return {'FINISHED'}

classes = (
    TOT_OT_GeoLODSetup,
    TOT_OT_GeoLODUpdate,
    TOT_OT_GeoLODReset,
    TOT_OT_GeoLODApply,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)