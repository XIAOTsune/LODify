import bmesh
import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.props import BoolProperty

from ..core.feature_analysis import score_bmesh_edge, trace_edge_paths
from .. import utils


_DRAW_HANDLER = None
_DEPSGRAPH_HANDLER = None
_ANALYSIS = None
_SHADER = None


def _remove_draw_handler():
    global _DRAW_HANDLER, _DEPSGRAPH_HANDLER, _ANALYSIS
    if _DRAW_HANDLER is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_DRAW_HANDLER, 'WINDOW')
        except (ReferenceError, RuntimeError, ValueError):
            pass
    _DRAW_HANDLER = None
    _ANALYSIS = None
    if _DEPSGRAPH_HANDLER is not None:
        try:
            bpy.app.handlers.depsgraph_update_post.remove(_DEPSGRAPH_HANDLER)
        except ValueError:
            pass
    _DEPSGRAPH_HANDLER = None


def clear_feature_analysis():
    _remove_draw_handler()


def _invalidate_analysis():
    global _DRAW_HANDLER, _ANALYSIS
    if _DRAW_HANDLER is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_DRAW_HANDLER, 'WINDOW')
        except (ReferenceError, RuntimeError, ValueError):
            pass
    _DRAW_HANDLER = None
    _ANALYSIS = None


def _draw_feature_paths():
    global _SHADER
    data = _ANALYSIS
    if not data:
        return

    obj = bpy.data.objects.get(data["object_name"])
    if obj is None or obj.type != 'MESH':
        return

    if _SHADER is None:
        try:
            _SHADER = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        except (RuntimeError, ValueError):
            return

    viewport = gpu.state.viewport_get()
    viewport_size = (viewport[2], viewport[3])
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')
    try:
        for key, color in (
            ("protected_paths", (0.1, 0.55, 1.0, 0.95)),
            ("candidate_paths", (1.0, 0.45, 0.05, 1.0)),
        ):
            for path in data[key]:
                points = [obj.matrix_world @ point for point in path]
                if len(points) < 2:
                    continue
                batch = batch_for_shader(_SHADER, 'LINE_STRIP', {"pos": points})
                _SHADER.bind()
                _SHADER.uniform_float("viewportSize", viewport_size)
                _SHADER.uniform_float("lineWidth", 3.0)
                _SHADER.uniform_float("color", color)
                batch.draw(_SHADER)
    finally:
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')


def _install_draw_handler():
    global _DRAW_HANDLER, _DEPSGRAPH_HANDLER
    if _DRAW_HANDLER is None:
        _DRAW_HANDLER = bpy.types.SpaceView3D.draw_handler_add(
            _draw_feature_paths, (), 'WINDOW', 'POST_VIEW'
        )
    if _DEPSGRAPH_HANDLER is None:
        _DEPSGRAPH_HANDLER = _clear_on_mesh_update
        bpy.app.handlers.depsgraph_update_post.append(_DEPSGRAPH_HANDLER)


def _clear_on_mesh_update(_scene, depsgraph):
    global _ANALYSIS
    if not _ANALYSIS:
        return
    obj = bpy.data.objects.get(_ANALYSIS["object_name"])
    if obj is None:
        _invalidate_analysis()
        return

    mesh_pointer = obj.data.as_pointer()
    for update in depsgraph.updates:
        try:
            updated_pointer = update.id.original.as_pointer()
        except (AttributeError, ReferenceError):
            continue
        if updated_pointer == mesh_pointer:
            _invalidate_analysis()
            return


def _build_feature_decimate(obj, edge_records, protection_strength, initial_ratio=1.0):
    protection = {}
    for record in edge_records:
        weight = 1.0 if record["kind"] == "protected" else min(1.0, max(0.0, record["score"]))
        for vertex_index in record["vertices"]:
            protection[vertex_index] = max(protection.get(vertex_index, 0.0), weight)

    # High Decimate group weights allow more modifier influence, so invert the
    # feature score and include every vertex to keep unmarked areas reducible.
    weights = {
        index: 1.0 - protection.get(index, 0.0)
        for index in range(len(obj.data.vertices))
    }

    old_group_name = obj.get("_lod_feature_group_name") if obj.get("_lod_feature_group_created") else None
    new_group = obj.vertex_groups.new(name="LODIFY_FEATURE_PROTECT")
    mod = None
    created_modifier = False
    old_vertex_group = None
    old_factor = None
    try:
        buckets = {}
        for vertex_index, weight in weights.items():
            buckets.setdefault(round(weight, 2), []).append(vertex_index)
        for weight, indices in buckets.items():
            new_group.add(indices, weight, 'REPLACE')

        mod = obj.modifiers.get("LOD_DECIMATE")
        created_modifier = mod is None
        if created_modifier:
            mod = obj.modifiers.new("LOD_DECIMATE", 'DECIMATE')
            mod.decimate_type = 'COLLAPSE'
        mod.ratio = initial_ratio
        if not hasattr(mod, "vertex_group_factor"):
            raise RuntimeError("This Blender version does not support Decimate vertex-group weighting.")

        old_vertex_group = mod.vertex_group
        old_factor = mod.vertex_group_factor
        mod.vertex_group = new_group.name
        mod.vertex_group_factor = protection_strength
        if obj.modifiers.get("LOD_GEO_LOD"):
            obj.modifiers.remove(obj.modifiers.get("LOD_GEO_LOD"))

        if old_group_name and old_group_name != new_group.name:
            old_group = obj.vertex_groups.get(old_group_name)
            if old_group:
                obj.vertex_groups.remove(old_group)

        obj["_lod_feature_group_name"] = new_group.name
        obj["_lod_feature_group_created"] = True
        obj["_lod_geo_lod_created"] = True
        return len(protection), created_modifier
    except Exception:
        if created_modifier and mod is not None:
            obj.modifiers.remove(mod)
        elif mod is not None and old_vertex_group is not None:
            mod.vertex_group = old_vertex_group
            mod.vertex_group_factor = old_factor
        group = obj.vertex_groups.get(new_group.name)
        if group:
            obj.vertex_groups.remove(group)
        raise


class LOD_OT_FeatureAnalysis(bpy.types.Operator):
    bl_idname = "lod.feature_analysis"
    bl_label = "Analyze Features"
    bl_description = "Analyze the active mesh without changing its geometry"
    bl_options = {'REGISTER', 'UNDO'}
    create_modifier: BoolProperty(default=False, options={'HIDDEN'})

    _timer = None
    _bm = None

    def invoke(self, context, event):
        global _ANALYSIS

        obj = context.object
        if obj is None or obj.type != 'MESH' or obj.mode != 'OBJECT':
            self.report({'ERROR'}, "Select an active mesh in Object Mode.")
            return {'CANCELLED'}
        if obj.data.shape_keys:
            self.report({'ERROR'}, "Feature analysis currently skips meshes with Shape Keys.")
            return {'CANCELLED'}
        min_faces = context.scene.lod_props.geo_lod_min_faces
        if self.create_modifier and min_faces > 0 and len(obj.data.polygons) < min_faces:
            self.report({'WARNING'}, f"Mesh has fewer than the {min_faces} face safety threshold.")
            return {'CANCELLED'}

        _remove_draw_handler()
        self._object_name = obj.name
        self._settings = {
            "angle_threshold_degrees": context.scene.lod_props.feature_angle_threshold,
            "min_path_edges": context.scene.lod_props.feature_min_path_edges,
            "protect_sharp": context.scene.lod_props.feature_protect_sharp,
            "protect_crease": context.scene.lod_props.feature_protect_crease,
            "protect_uv": context.scene.lod_props.feature_protect_uv,
            "protect_seam": context.scene.lod_props.feature_protect_seam,
            "protect_material": context.scene.lod_props.feature_protect_material,
        }
        self._protection_strength = context.scene.lod_props.feature_protect_strength
        self._bm = bmesh.new()
        try:
            self._bm.from_mesh(obj.data)
            self._bm.verts.ensure_lookup_table()
            self._bm.edges.ensure_lookup_table()
            self._bm.faces.ensure_lookup_table()
            self._bm.verts.index_update()
            self._bm.edges.index_update()
            self._bm.faces.index_update()
        except Exception as error:
            self._bm.free()
            self._bm = None
            self.report({'ERROR'}, f"Could not read mesh: {error}")
            return {'CANCELLED'}

        self._edge_index = 0
        self._edge_records = []
        self._total_edges = len(self._bm.edges)
        self._uv_layer = self._bm.loops.layers.uv.active
        self._crease_layer = getattr(self._bm.edges.layers.float, "get", lambda _name: None)("crease_edge")
        wm = context.window_manager
        wm.progress_begin(0, max(1, self._total_edges))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        try:
            stop_at = min(self._edge_index + 400, self._total_edges)
            while self._edge_index < stop_at:
                edge = self._bm.edges[self._edge_index]
                record = score_bmesh_edge(edge, self._uv_layer, self._crease_layer, self._settings)
                if record is not None:
                    self._edge_records.append(record)
                self._edge_index += 1

            context.window_manager.progress_update(self._edge_index)
            if self._edge_index >= self._total_edges:
                return self.finish(context)
        except Exception as error:
            self.report({'ERROR'}, f"Feature analysis failed: {error}")
            return self.cancel(context)
        return {'PASS_THROUGH'}

    def finish(self, context):
        global _ANALYSIS
        obj = bpy.data.objects.get(self._object_name)
        if obj is None:
            return self.cancel(context)

        protected = [item for item in self._edge_records if item["kind"] == "protected"]
        candidates = [item for item in self._edge_records if item["kind"] == "candidate"]
        min_path_edges = self._settings["min_path_edges"]
        protected_paths = trace_edge_paths(protected, min_edges=min_path_edges)
        candidate_paths = trace_edge_paths(candidates, min_edges=min_path_edges)
        accepted_candidate_indices = {
            edge_index
            for path in candidate_paths
            for edge_index in path["edge_indices"]
        }
        accepted_records = protected + [
            item for item in candidates if item["edge_index"] in accepted_candidate_indices
        ]
        vertices = [vertex.co.copy() for vertex in self._bm.verts]
        _ANALYSIS = {
            "object_name": obj.name,
            "mesh_pointer": obj.data.as_pointer(),
            "protected_paths": [
                [vertices[index] for index in path["vertex_indices"]]
                for path in protected_paths
            ],
            "candidate_paths": [
                [vertices[index] for index in path["vertex_indices"]]
                for path in candidate_paths
            ],
        }

        protected_count = sum(item["kind"] == "protected" for item in self._edge_records)
        candidate_count = len(self._edge_records) - protected_count
        if self.create_modifier:
            try:
                props = context.scene.lod_props
                camera = props.lod_camera or context.scene.camera
                initial_ratio = 1.0
                screen_ratio = None
                if camera is not None:
                    screen_ratio = utils.get_normalized_screen_ratio(context.scene, obj, camera)
                    initial_ratio = utils.get_feature_guided_lod_factor(
                        screen_ratio, props.geo_lod_min_ratio
                    )
                weight_count, created_modifier = _build_feature_decimate(
                    obj, accepted_records, self._protection_strength, initial_ratio
                )
            except Exception as error:
                _ANALYSIS = None
                self.report({'ERROR'}, f"Could not build guided Decimate: {error}")
                return self.cancel(context)

        self._cleanup(context)
        _install_draw_handler()
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        if self.create_modifier:
            mode = "updated" if not created_modifier else "created"
            ratio_message = (
                f" at ratio {initial_ratio:.3f} (screen {screen_ratio:.3f})"
                if screen_ratio is not None else " at ratio 1.000 (no LOD camera)"
            )
            self.report(
                {'INFO'},
                f"Analyzed {self._total_edges} edges; {mode} guided Decimate{ratio_message}; "
                f"{weight_count} protected vertices, {len(accepted_records)} weighted feature edges.",
            )
        else:
            self.report(
                {'INFO'},
                f"Analyzed {self._total_edges} edges: {len(protected_paths)} protected paths, "
                f"{len(candidate_paths)} feature paths.",
            )
        return {'FINISHED'}

    def _cleanup(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        if self._bm is not None:
            self._bm.free()
            self._bm = None

    def cancel(self, context):
        self._cleanup(context)
        self.report({'INFO'}, "Feature analysis cancelled.")
        return {'CANCELLED'}


class LOD_OT_FeatureAnalysisClear(bpy.types.Operator):
    bl_idname = "lod.feature_analysis_clear"
    bl_label = "Clear Feature Analysis"
    bl_description = "Remove feature-analysis overlays"
    bl_options = {'REGISTER'}

    def execute(self, context):
        clear_feature_analysis()
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


classes = (LOD_OT_FeatureAnalysis, LOD_OT_FeatureAnalysisClear)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    clear_feature_analysis()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
