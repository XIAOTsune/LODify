import json

import bpy

from .. import utils


def _get_view3d_shading(context):
    space_data = getattr(context, "space_data", None)
    if not space_data or space_data.type != 'VIEW_3D':
        return None
    return getattr(space_data, "shading", None)


class LOD_OT_CollectionAnalyzer(bpy.types.Operator):
    """Analyzes collection vertex counts and color-codes them"""
    bl_idname = "lod.collectionanalyzer"
    bl_label = "Run Analyzer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.lod_props
        bpy.ops.lod.cleancolors()

        self.report({'INFO'}, "Analyzing Collections...")

        if scn.colA_Method == 'm1':
            m_vhigh, m_high, m_med, m_low = 0.9, 0.8, 0.6, 0.2
        else:
            m_vhigh = scn.mult_veryhigh
            m_high = scn.mult_high
            m_med = scn.mult_medium
            m_low = scn.mult_low

        backup = {}
        scene_total_verts = 0
        use_heatmap = scn.CA_use_heatmap

        for obj in context.view_layer.objects:
            if obj.type == 'MESH':
                scene_total_verts += len(obj.data.vertices)

        if scene_total_verts == 0:
            scene_total_verts = 1

        for col in bpy.data.collections:
            backup[col.name] = col.color_tag

            if use_heatmap:
                col.color_tag = 'NONE'

            v_count = utils.get_collection_vertex_count(col)
            if v_count <= 0:
                continue

            percent = (v_count / scene_total_verts) * 100.0
            col.name = f"{col.name} | {percent:.1f}%"

            if use_heatmap:
                ratio = v_count / scene_total_verts
                if ratio >= m_vhigh:
                    col.color_tag = 'COLOR_01'
                elif ratio >= m_high:
                    col.color_tag = 'COLOR_02'
                elif ratio >= m_med:
                    col.color_tag = 'COLOR_03'
                elif ratio >= m_low:
                    col.color_tag = 'COLOR_04'
                else:
                    col.color_tag = 'COLOR_05'

        scn.default_col_colors = json.dumps(backup)
        scn.CA_Toggle = True
        return {'FINISHED'}


class LOD_OT_CleanColors(bpy.types.Operator):
    """Restores original collection names and colors"""
    bl_idname = "lod.cleancolors"
    bl_label = "Clear Analyzer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.lod_props
        data = {}

        if scn.default_col_colors:
            try:
                data = json.loads(scn.default_col_colors)
            except Exception as e:
                print(f"LODify Error loading colors: {e}")

        for col in bpy.data.collections:
            base_name = col.name.split(' | ')[0].strip() if ' | ' in col.name else col.name
            if base_name in data:
                col.color_tag = data[base_name]
            if ' | ' in col.name:
                col.name = base_name

        scn.CA_Toggle = False
        scn.default_col_colors = ""
        return {'FINISHED'}


class LOD_OT_ViewAnalyzer(bpy.types.Operator):
    """Analyzes objects in 3D view and color-codes by density"""
    bl_idname = "lod.viewanalyzer"
    bl_label = "Run 3D View Analyzer"

    def execute(self, context):
        scn = context.scene.lod_props
        shading = _get_view3d_shading(context)
        if shading and hasattr(shading, "color_type"):
            scn.last_shading = shading.color_type
            shading.type = 'SOLID'
            shading.color_type = 'OBJECT'

        max_v = 1
        mesh_objs = [o for o in context.view_layer.objects if o.type == 'MESH']
        for obj in mesh_objs:
            max_v = max(max_v, len(obj.data.vertices))

        from mathutils import Color

        for obj in mesh_objs:
            if "_lod_orig_color" not in obj:
                obj["_lod_orig_color"] = list(obj.color)

            ratio = len(obj.data.vertices) / max_v
            color = Color()
            color.hsv = (0.66 * (1.0 - ratio), 1.0, 1.0)
            obj.color = (color.r, color.g, color.b, 1.0)

        scn.AA_Toggle = True
        return {'FINISHED'}


class LOD_OT_CleanViewAnalyzer(bpy.types.Operator):
    """Clear View Analyzer"""
    bl_idname = "lod.cleanviewanalyzer"
    bl_label = "Clear View Analyzer"

    def execute(self, context):
        scn = context.scene.lod_props
        shading = _get_view3d_shading(context)
        if shading and hasattr(shading, "color_type"):
            target = scn.last_shading if scn.last_shading else 'MATERIAL'
            try:
                shading.color_type = target
            except Exception:
                pass

        for obj in context.view_layer.objects:
            if "_lod_orig_color" in obj:
                try:
                    obj.color = tuple(obj["_lod_orig_color"])
                except Exception:
                    obj.color = (1, 1, 1, 1)
                del obj["_lod_orig_color"]

        scn.AA_Toggle = False
        return {'FINISHED'}


classes = (
    LOD_OT_CollectionAnalyzer,
    LOD_OT_CleanColors,
    LOD_OT_ViewAnalyzer,
    LOD_OT_CleanViewAnalyzer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
