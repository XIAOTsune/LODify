import json
import os

import bpy

from .. import utils
from ..properties import get_animation_settings_snapshot
from . import geometry
from .image import _image_worker_limit, _start_image_worker


def _camera_cut_frames(scene, start, end):
    frames = set()
    for marker in scene.timeline_markers:
        if marker.camera and start <= marker.frame <= end:
            frames.update((marker.frame - 1, marker.frame, marker.frame + 1))
    return {frame for frame in frames if start <= frame <= end}


def _camera_for_frame(scene, frame, explicit_camera=None, fallback_camera=None):
    if explicit_camera:
        return explicit_camera

    camera = fallback_camera or scene.camera
    for marker in sorted(scene.timeline_markers, key=lambda item: item.frame):
        if marker.frame > frame:
            break
        if marker.camera:
            camera = marker.camera
    return camera


def _is_animated_mesh_supported(obj):
    if obj.data.shape_keys:
        return "Shape keys"
    animation_data = obj.animation_data
    if animation_data:
        allowed_paths = {"location", "rotation_euler", "rotation_quaternion", "scale"}
        action = animation_data.action
        channels = getattr(action, "fcurves", ()) if action else ()
        if action and not hasattr(action, "fcurves"):
            return "Animation channels unavailable"
        if any(curve.data_path not in allowed_paths for curve in channels):
            return "Animated non-transform properties"
        if any(driver.data_path not in allowed_paths for driver in getattr(animation_data, "drivers", ())):
            return "Driven non-transform properties"
    if obj.data.animation_data:
        return "Animated mesh data"
    for modifier in obj.modifiers:
        if modifier.name in {geometry.DECIMATE_MOD_NAME, geometry.GEO_NODES_MOD_NAME}:
            continue
        if getattr(modifier, "animation_data", None):
            return "Animated modifier settings"
        if modifier.type in {'ARMATURE', 'CLOTH', 'SOFT_BODY', 'FLUID', 'DYNAMIC_PAINT', 'NODES', 'MESH_SEQUENCE_CACHE'}:
            return f"{modifier.type.title()} modifier"
    return ""


def _iter_image_nodes(obj):
    for slot in obj.material_slots:
        material = slot.material
        if material and material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    yield node


class LOD_OT_AnimationAnalyze(bpy.types.Operator):
    bl_idname = "lod.animation_analyze"
    bl_label = "Analyze Animation"
    bl_options = {'REGISTER'}

    _timer = None

    def invoke(self, context, event):
        scene = context.scene
        props = scene.lod_props
        self.scene = scene
        self.old_frame = scene.frame_current
        self.old_subframe = scene.frame_subframe
        self.old_camera = scene.camera
        self.fallback_camera = scene.camera
        self.explicit_camera = props.animation_camera
        self.settings_snapshot = get_animation_settings_snapshot(scene)
        self.start = scene.frame_start
        self.end = scene.frame_end
        step = max(1, props.animation_sample_step)
        frames = set(range(self.start, self.end + 1, step))
        frames.update((self.start, self.end))
        frames.update(_camera_cut_frames(scene, self.start, self.end))
        self.frames = sorted(frames)
        self.index = 0
        self.results = {}
        self.skipped = {}
        self.images = {}
        self.disabled_modifiers = []
        for obj in scene.objects:
            for modifier in obj.modifiers:
                if modifier.name in {geometry.DECIMATE_MOD_NAME, geometry.GEO_NODES_MOD_NAME}:
                    self.disabled_modifiers.append((modifier, modifier.show_viewport, modifier.show_render))
                    modifier.show_viewport = False
                    modifier.show_render = False
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self.restore(context)
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        if self.index < len(self.frames):
            frame = self.frames[self.index]
            self.scene.frame_set(frame)
            camera = _camera_for_frame(
                self.scene,
                frame,
                self.explicit_camera,
                self.fallback_camera,
            )
            if camera:
                depsgraph = context.evaluated_depsgraph_get()
                eval_camera = camera.evaluated_get(depsgraph)
                for obj in self.scene.objects:
                    if obj.type != 'MESH' or obj.hide_render:
                        continue
                    reason = _is_animated_mesh_supported(obj)
                    if reason:
                        self.skipped[obj.name] = reason
                    evaluated = obj.evaluated_get(depsgraph)
                    pixels, visible = utils.calculate_screen_coverage(self.scene, evaluated, eval_camera)
                    ratio = utils.get_normalized_screen_ratio(self.scene, evaluated, eval_camera)
                    record = self.results.setdefault(obj.name, {"peak": 0.0, "frame": frame, "object": obj, "images": set()})
                    if ratio > record["peak"]:
                        record["peak"] = ratio
                        record["frame"] = frame
                    for node in _iter_image_nodes(obj):
                        image = node.image
                        record["images"].add(image.name)
                        if image.source in {'MOVIE', 'SEQUENCE', 'TILED', 'GENERATED', 'VIEWER'}:
                            self.skipped[f"Image: {image.name}"] = "Movie, image sequence, UDIM, or generated image"
                            continue
                        if not image.filepath or not os.path.isfile(bpy.path.abspath(image.filepath)):
                            self.skipped[f"Image: {image.name}"] = "Packed image or source file unavailable"
                            continue
                        if visible and image.size[0] > 0:
                            cap = int(self.scene.lod_props.custom_resize_size if self.scene.lod_props.resize_size == 'c' else self.scene.lod_props.resize_size)
                            demand = min(max(pixels * self.scene.lod_props.animation_texture_scale, 32), cap, max(image.size))
                            current = self.images.get(image.name)
                            if current is None or demand > current["demand"]:
                                self.images[image.name] = {"image": image, "demand": demand, "frame": frame}
            self.index += 1
            return {'RUNNING_MODAL'}
        self.finish(context)
        for name, item in self.results.items():
            if item["peak"] <= 0 and name not in self.skipped:
                self.skipped[name] = "Outside camera view for all sampled frames"
            elif self.scene.lod_props.geo_lod_min_faces and len(item["object"].data.polygons) < self.scene.lod_props.geo_lod_min_faces:
                self.skipped[name] = "Below minimum face count"
        payload = {
            "frames": self.frames,
            "objects": [{"name": name, "peak": item["peak"], "frame": item["frame"], "images": sorted(item["images"])} for name, item in self.results.items()],
            "images": [{"name": name, "demand": item["demand"], "frame": item["frame"], "width": item["image"].size[0], "height": item["image"].size[1]} for name, item in self.images.items()],
            "skipped": self.skipped,
            "camera_mode": "explicit" if self.explicit_camera else "timeline",
            "settings": self.settings_snapshot,
        }
        context.scene.lod_props.animation_report = json.dumps(payload)
        self.report({'INFO'}, f"Analyzed {len(self.frames)} frames, {len(self.results)} meshes, {len(self.images)} images")
        return {'FINISHED'}

    def restore(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        for modifier, viewport, render in self.disabled_modifiers:
            if modifier.id_data:
                modifier.show_viewport = viewport
                modifier.show_render = render
        self.scene.frame_set(self.old_frame, subframe=self.old_subframe)
        self.scene.camera = self.old_camera

    def finish(self, context):
        self.restore(context)


class LOD_OT_AnimationGenerate(bpy.types.Operator):
    bl_idname = "lod.animation_generate"
    bl_label = "Generate Animation Copy"
    bl_options = {'REGISTER'}

    _timer = None

    def execute(self, context):
        scene = context.scene
        try:
            report = json.loads(scene.lod_props.animation_report)
        except (TypeError, ValueError):
            self.report({'ERROR'}, "Analyze the animation first")
            return {'CANCELLED'}
        if report.get("settings") != get_animation_settings_snapshot(scene):
            self.report({'ERROR'}, "Settings changed. Analyze the animation again before generating the copy")
            return {'CANCELLED'}
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the project before generating an optimized copy")
            return {'CANCELLED'}
        root, ext = os.path.splitext(bpy.data.filepath)
        self.output_blend = root + "_animation_optimized.blend"
        self.output_textures = root + "_animation_textures"
        os.makedirs(self.output_textures, exist_ok=True)
        self.report_data = report
        self.scene = scene
        self.object_settings = {item["name"]: item for item in report["objects"]}
        self.image_tasks = []
        self.created_images = []
        self.changed_nodes = []
        self.added_modifiers = []
        self.created_node_groups = []
        max_texture_size = int(scene.lod_props.custom_resize_size if scene.lod_props.resize_size == 'c' else scene.lod_props.resize_size)
        for item in report["images"]:
            image = bpy.data.images.get(item["name"])
            if not image or image.source != 'FILE' or not image.filepath:
                continue
            source = bpy.path.abspath(image.filepath)
            ext = os.path.splitext(source)[1]
            target_size = _round_image_size(item["demand"], max(image.size), max_texture_size)
            safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in image.name)
            filename = safe_name + f"_{target_size}px" + ext
            destination = os.path.join(self.output_textures, filename)
            action = "COPY" if ext.lower() in {'.hdr', '.exr'} else "RESIZE"
            self.image_tasks.append({"img_name": image.name, "src_path": source, "dst_path": destination, "target_size": target_size, "action": action, "method": "PIL"})
        self.active = []
        self.queue = list(self.image_tasks)
        self.worker_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "image_worker.py")
        self.worker_limit = _image_worker_limit()
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            for proc, _task in self.active:
                proc.terminate()
            self.restore()
            context.window_manager.event_timer_remove(self._timer)
            self.report({'WARNING'}, "Generation cancelled")
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        for index in range(len(self.active) - 1, -1, -1):
            process, task = self.active[index]
            if process.poll() is None:
                continue
            stdout, stderr = process.communicate()
            if process.returncode != 0 or "SUCCESS" not in stdout:
                for active_process, _active_task in self.active:
                    active_process.terminate()
                self.report({'ERROR'}, f"Texture processing failed for {task['img_name']}: {stderr[:180]}")
                self.cleanup(context)
                context.window_manager.event_timer_remove(self._timer)
                return {'CANCELLED'}
            self.active.pop(index)
        while self.queue and len(self.active) < self.worker_limit:
            task = self.queue.pop(0)
            self.active.append((_start_image_worker(self.worker_script, task), task))
        if not self.queue and not self.active:
            try:
                self.write_optimized_copy()
                self.cleanup(context)
                context.window_manager.event_timer_remove(self._timer)
                self.report({'INFO'}, f"Wrote {self.output_blend}")
                return {'FINISHED'}
            except Exception as error:
                self.report({'ERROR'}, f"Could not write optimized copy: {error}")
                self.cleanup(context)
                context.window_manager.event_timer_remove(self._timer)
                return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def write_optimized_copy(self):
        for item in self.image_tasks:
            image = bpy.data.images.get(item["img_name"])
            if not image:
                continue
            output_image = bpy.data.images.load(item["dst_path"], check_existing=False)
            self.created_images.append(output_image)
            for obj in self.scene.objects:
                for node in _iter_image_nodes(obj):
                    if node.image == image:
                        self.changed_nodes.append((node, image))
                        node.image = output_image
        method = self.scene.lod_props.geo_lod_method
        for item in self.report_data["objects"]:
            obj = self.scene.objects.get(item["name"])
            if not obj or obj.type != 'MESH' or item["peak"] <= 0:
                continue
            if _is_animated_mesh_supported(obj):
                continue
            if self.scene.lod_props.geo_lod_min_faces and len(obj.data.polygons) < self.scene.lod_props.geo_lod_min_faces:
                continue
            factor = utils.get_stepped_lod_factor(item["peak"], self.scene.lod_props.geo_lod_min_ratio)
            if method == 'DECIMATE':
                modifier = obj.modifiers.new("LOD_ANIMATION_DECIMATE", 'DECIMATE')
                self.added_modifiers.append((obj, modifier))
                modifier.ratio = factor
            else:
                node_group = bpy.data.node_groups.get(geometry.GN_GROUP_NAME)
                if node_group is None:
                    node_group = geometry.ensure_lod_node_group()
                    self.created_node_groups.append(node_group)
                modifier = obj.modifiers.new("LOD_ANIMATION_NODES", 'NODES')
                self.added_modifiers.append((obj, modifier))
                modifier.node_group = node_group
                factor_id = geometry.get_input_identifier(node_group, geometry.GN_INPUT_FACTOR)
                dist_id = geometry.get_input_identifier(node_group, geometry.GN_INPUT_MAX_DIST)
                if not factor_id or not dist_id:
                    raise RuntimeError("Existing Geometry LOD node group is missing required inputs")
                geometry._set_geometry_node_input(modifier, factor_id, factor)
                geometry._set_geometry_node_input(modifier, dist_id, self.scene.lod_props.geo_lod_max_dist)
        bpy.data.libraries.write(self.output_blend, {self.scene}, path_remap='RELATIVE')

    def restore(self):
        for node, image in self.changed_nodes:
            if node.id_data:
                node.image = image
        for obj, modifier in self.added_modifiers:
            if obj and modifier in obj.modifiers[:]:
                obj.modifiers.remove(modifier)
        for image in self.created_images:
            if image.users == 0:
                bpy.data.images.remove(image)
        for node_group in self.created_node_groups:
            if node_group.users == 0:
                bpy.data.node_groups.remove(node_group)

    def cleanup(self, context):
        self.restore()


def _round_image_size(value, source_size, max_size):
    limit = min(max(4, int(value)), max(4, int(source_size)), max(4, int(max_size)))
    for size in (4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096):
        if size >= limit:
            return min(size, limit)
    return limit


classes = (LOD_OT_AnimationAnalyze, LOD_OT_AnimationGenerate)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
