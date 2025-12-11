import bpy
from mathutils import Vector

# 定义常量，保持与 v2 一致
DECIMATE_MOD_NAME = "TOT_LOD_DECIMATE"
GEO_NODES_MOD_NAME = "TOT_GEO_LOD"

# --- Helper: 节点组逻辑 (保持核心功能) ---
def ensure_lod_node_group():
    """确保存在一个几何 LOD 节点组 (v2 逻辑)"""
    name = "TOT_GEO_LOD_Basic"
    group = bpy.data.node_groups.get(name)
    if not group:
        group = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
        
        # 兼容 Blender 4.0+ 接口
        if hasattr(group, "interface"):
            group.interface.clear()
            group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            sock_factor = group.interface.new_socket(name="LOD_Factor", in_out='INPUT', socket_type='NodeSocketFloat')
            sock_factor.min_value = 0.0
            sock_factor.max_value = 1.0
            sock_factor.default_value = 0.0
            group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
        nodes = group.nodes
        links = group.links
        nodes.clear()
        
        # 基础节点
        input_node = nodes.new("NodeGroupInput")
        output_node = nodes.new("NodeGroupOutput")
        input_node.location = (-400, 0)
        output_node.location = (400, 0)
        
        # v2 的核心逻辑：Merge By Distance
        # Distance = (BBox Diagonal * 0.1) * LOD_Factor
        
        # 1. 计算 BBox 对角线
        node_bbox = nodes.new("GeometryNodeBoundBox")
        node_bbox.location = (-200, 200)
        
        node_sub = nodes.new("ShaderNodeVectorMath")
        node_sub.operation = 'SUBTRACT'
        node_sub.location = (0, 200)
        
        node_len = nodes.new("ShaderNodeVectorMath")
        node_len.operation = 'LENGTH'
        node_len.location = (160, 200)
        
        # 2. 计算基准距离 (0.1 系数)
        node_math_base = nodes.new("ShaderNodeMath")
        node_math_base.operation = 'MULTIPLY'
        node_math_base.inputs[1].default_value = 0.1
        node_math_base.location = (320, 200)
        
        # 3. 乘上 LOD Factor
        node_math_final = nodes.new("ShaderNodeMath")
        node_math_final.operation = 'MULTIPLY'
        node_math_final.location = (320, 0)
        
        # 4. Merge
        node_merge = nodes.new("GeometryNodeMergeByDistance")
        node_merge.location = (500, 0)
        
        # 连线
        links.new(input_node.outputs["Geometry"], node_merge.inputs["Geometry"])
        links.new(input_node.outputs["Geometry"], node_bbox.inputs["Geometry"])
        
        links.new(node_bbox.outputs["Min"], node_sub.inputs[0])
        links.new(node_bbox.outputs["Max"], node_sub.inputs[1])
        links.new(node_sub.outputs["Vector"], node_len.inputs["Vector"])
        links.new(node_len.outputs["Value"], node_math_base.inputs[0])
        
        links.new(node_math_base.outputs["Value"], node_math_final.inputs[0])
        links.new(input_node.outputs["LOD_Factor"], node_math_final.inputs[1])
        
        links.new(node_math_final.outputs["Value"], node_merge.inputs["Distance"])
        links.new(node_merge.outputs["Geometry"], output_node.inputs["Geometry"])

    return group

# --- Operators (v2 Logic) ---

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
            # 最小面数检查
            if min_faces > 0 and len(obj.data.polygons) < min_faces: continue
            
            if method == 'DECIMATE':
                mod = obj.modifiers.get(DECIMATE_MOD_NAME)
                if not mod:
                    mod = obj.modifiers.new(DECIMATE_MOD_NAME, 'DECIMATE')
                    mod.decimate_type = 'COLLAPSE'
                    mod.ratio = 1.0
                    obj["_tot_geo_lod_created"] = True # 标记
                    created += 1
                    
            elif method == 'GNODES':
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
        if not cam: return {'CANCELLED'}
        
        cam_loc = cam.matrix_world.translation
        d0, d1, d2 = scn.lod_dist_0, scn.lod_dist_1, scn.lod_dist_2
        method = scn.geo_lod_method
        
        updated = 0
        
        for obj in context.scene.objects:
            if obj.type != 'MESH': continue
            
            # 计算距离 (使用包围盒中心，v2逻辑)
            try:
                bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                center = sum(bbox_world, Vector()) / 8.0
            except:
                center = obj.matrix_world.translation
            
            dist = (center - cam_loc).length
            
            # 4级判定 (v2逻辑)
            if dist <= d0: level = 0
            elif dist <= d1: level = 1
            elif dist <= d2: level = 2
            else: level = 3
            
            # 归一化因子 (0.0 - 1.0)
            factor = level / 3.0
            
            if method == 'DECIMATE':
                mod = obj.modifiers.get(DECIMATE_MOD_NAME)
                if mod:
                    # Ratio: 1.0 -> min_ratio
                    min_ratio = scn.geo_lod_min_ratio
                    ratio = 1.0 - factor * (1.0 - min_ratio)
                    mod.ratio = ratio
                    updated += 1
            
            elif method == 'GNODES':
                mod = obj.modifiers.get(GEO_NODES_MOD_NAME)
                if mod:
                    # 尝试写入 LOD_Factor
                    try:
                        # 4.0+ 方式或兼容旧版
                        mod["LOD_Factor"] = factor
                        updated += 1
                    except: pass
                    
        self.report({'INFO'}, f"Updated {updated} objects.")
        return {'FINISHED'}

class TOT_OT_GeoLODReset(bpy.types.Operator):
    """Reset / Remove Modifiers"""
    bl_idname = "tot.geo_lod_reset"
    bl_label = "Reset Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed = 0
        for obj in context.scene.objects:
            # 移除标记为插件创建的修改器
            if obj.get("_tot_geo_lod_created", False):
                mod_dec = obj.modifiers.get(DECIMATE_MOD_NAME)
                if mod_dec: obj.modifiers.remove(mod_dec)
                
                mod_gn = obj.modifiers.get(GEO_NODES_MOD_NAME)
                if mod_gn: obj.modifiers.remove(mod_gn)
                
                del obj["_tot_geo_lod_created"]
                removed += 1
            else:
                # 即使没有标记，如果名字匹配也尝试移除 (更彻底的清理)
                mod_dec = obj.modifiers.get(DECIMATE_MOD_NAME)
                if mod_dec: 
                    obj.modifiers.remove(mod_dec)
                    removed += 1
                    
                mod_gn = obj.modifiers.get(GEO_NODES_MOD_NAME)
                if mod_gn: 
                    obj.modifiers.remove(mod_gn)
                    removed += 1

        self.report({'INFO'}, f"Reset complete. Cleaned {removed} objects.")
        return {'FINISHED'}

class TOT_OT_GeoLODApply(bpy.types.Operator):
    """Apply Decimate Modifier"""
    bl_idname = "tot.geo_lod_apply"
    bl_label = "Apply (Destructive)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 仅支持 Decimate 模式 (v2 逻辑)
        scn = context.scene.tot_props
        if scn.geo_lod_method != 'DECIMATE':
            self.report({'WARNING'}, "Apply only works with Decimate method.")
            return {'CANCELLED'}
        
        # 切换到 Object 模式
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        applied = 0
        
        # 收集目标
        targets = [o for o in context.scene.objects if o.type == 'MESH' and o.modifiers.get(DECIMATE_MOD_NAME)]
        
        # 保存选择状态
        active_old = context.view_layer.objects.active
        selected_old = context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in targets:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            try:
                bpy.ops.object.modifier_apply(modifier=DECIMATE_MOD_NAME)
                if "_tot_geo_lod_created" in obj:
                    del obj["_tot_geo_lod_created"]
                applied += 1
            except Exception as e:
                print(f"Apply failed on {obj.name}: {e}")
            obj.select_set(False)
            
        # 恢复选择
        for o in selected_old:
            try: o.select_set(True)
            except: pass
        if active_old:
            context.view_layer.objects.active = active_old
            
        self.report({'INFO'}, f"Applied Decimate to {applied} objects.")
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