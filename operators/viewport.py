import bpy
from mathutils import Vector


DISPLAY_RANKS = {
    'TEXTURED': 3,
    'SOLID': 2,
    'WIRE': 1,
    'BOUNDS': 0,
}


def _get_supported_display_types():
    enum_items = bpy.types.Object.bl_rna.properties["display_type"].enum_items
    return [item.identifier for item in enum_items]


def _normalize_display_type(value):
    supported = _get_supported_display_types()
    if value in supported:
        return value
    if 'SOLID' in supported:
        return 'SOLID'
    return supported[0]


class LOD_OT_ViewportLODUpdate(bpy.types.Operator):
    """Update Viewport Display Mode Based on Distance (Solid / Wire / Bounds)"""
    bl_idname = "lod.viewport_lod_update"
    bl_label = "Update Viewport LOD"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.lod_props

        if not scn.view_lod_enabled:
            self.report({'WARNING'}, "Viewport LOD is disabled in settings.")
            return {'CANCELLED'}

        cam = scn.lod_camera or context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No Camera found for LOD calculation.")
            return {'CANCELLED'}

        cam_loc = cam.matrix_world.translation
        d0, d1, d2 = scn.lod_dist_0, scn.lod_dist_1, scn.lod_dist_2
        count = 0

        for obj in context.scene.objects:
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue

            if "_lod_orig_display" not in obj:
                obj["_lod_orig_display"] = obj.display_type
            if "_lod_orig_hide" not in obj:
                obj["_lod_orig_hide"] = int(obj.hide_viewport)

            try:
                bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                center = sum(bbox_world, Vector()) / 8.0
            except Exception:
                center = obj.matrix_world.translation

            dist = (center - cam_loc).length
            if dist <= d0:
                level = 0
            elif dist <= d1:
                level = 1
            elif dist <= d2:
                level = 2
            else:
                level = 3

            attr_name = f"view_lod{level}_display"
            target_display = _normalize_display_type(getattr(scn, attr_name, 'BOUNDS'))
            orig_display = _normalize_display_type(obj.get("_lod_orig_display", 'TEXTURED'))

            rank_target = DISPLAY_RANKS.get(target_display, 2)
            rank_orig = DISPLAY_RANKS.get(orig_display, 2)
            final_display = target_display if rank_target < rank_orig else orig_display

            should_hide_by_lod = level == 3 and scn.view_lod3_hide
            orig_is_hidden = bool(obj.get("_lod_orig_hide", 0))

            obj.display_type = _normalize_display_type(final_display)
            obj.hide_viewport = should_hide_by_lod or orig_is_hidden
            count += 1

        self.report({'INFO'}, f"Viewport LOD Updated: {count} objects processed (Downgrade Only).")
        return {'FINISHED'}


class LOD_OT_ViewportLODReset(bpy.types.Operator):
    """Restore Original Display Mode"""
    bl_idname = "lod.viewport_lod_reset"
    bl_label = "Reset Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restored_count = 0

        for obj in context.scene.objects:
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue

            if "_lod_orig_display" in obj:
                try:
                    obj.display_type = _normalize_display_type(obj["_lod_orig_display"])
                except Exception:
                    obj.display_type = _normalize_display_type('TEXTURED')
                del obj["_lod_orig_display"]
                restored_count += 1

            if "_lod_orig_hide" in obj:
                obj.hide_viewport = bool(obj["_lod_orig_hide"])
                del obj["_lod_orig_hide"]

        self.report({'INFO'}, f"Reset Viewport: Restored {restored_count} objects.")
        return {'FINISHED'}


classes = (
    LOD_OT_ViewportLODUpdate,
    LOD_OT_ViewportLODReset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
