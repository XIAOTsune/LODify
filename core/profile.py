import json
import time
import uuid

import bpy
from bpy.props import CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty


PROFILE_SCHEMA_VERSION = 1
UUID_KEY = "_lodify_uuid"
GENERATED_PROFILE_KEY = "_lodify_profile_id"


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    try:
        return [_json_safe(item) for item in value]
    except TypeError:
        return str(value)


class LODIFY_Profile(bpy.types.PropertyGroup):
    profile_id: StringProperty(name="Profile ID")
    name: StringProperty(name="Profile Name", default="Render Profile")
    camera: PointerProperty(name="Render Camera", type=bpy.types.Object)
    scope_collection: PointerProperty(name="Scope Collection", type=bpy.types.Collection)
    generated_root: StringProperty(name="Generated Assets", subtype="DIR_PATH")
    status: EnumProperty(
        name="Status",
        items=[
            ("NEW", "New", "No snapshot has been captured"),
            ("CAPTURED", "Ready", "Original scene state is recorded"),
            ("RESTORED", "Restored", "Original scene state was restored"),
            ("ERROR", "Error", "The last profile operation failed"),
        ],
        default="NEW",
    )
    snapshot_json: StringProperty(options={"HIDDEN"})
    snapshot_text_name: StringProperty(options={"HIDDEN"})
    last_report: StringProperty(options={"HIDDEN"})
    created_at: StringProperty(options={"HIDDEN"})


class LODIFY_UL_Profiles(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.name, icon="CAMERA_DATA" if item.camera else "FILE_BLEND")
        row.label(text=item.status)


def _ensure_uuid(id_block):
    if id_block is None:
        return ""
    try:
        value = id_block.get(UUID_KEY)
        if value:
            return str(value)
        value = uuid.uuid4().hex
        id_block[UUID_KEY] = value
        return value
    except Exception:
        # Linked/read-only datablocks cannot always accept custom properties.
        return f"name:{getattr(id_block, 'name', '')}"


def _find_by_uuid(collection, value):
    if not value:
        return None
    for item in collection:
        try:
            if str(item.get(UUID_KEY, "")) == value:
                return item
        except Exception:
            continue
    if value.startswith("name:"):
        return collection.get(value[5:])
    return None


def _scene_objects(scene, profile):
    if profile.scope_collection:
        return list(profile.scope_collection.all_objects)
    return list(scene.objects)


def get_active_profile(scene):
    profiles = getattr(scene, "lodify_profiles", None)
    if not profiles:
        return None
    index = min(max(scene.lodify_active_profile, 0), len(profiles) - 1)
    scene.lodify_active_profile = index
    return profiles[index]


def create_profile(scene, name=None):
    profile = scene.lodify_profiles.add()
    profile.profile_id = uuid.uuid4().hex
    profile.name = name or f"Render Profile {len(scene.lodify_profiles)}"
    profile.camera = scene.camera if scene.camera and scene.camera.type == "CAMERA" else None
    profile.created_at = str(time.time())
    scene.lodify_active_profile = len(scene.lodify_profiles) - 1
    return profile


def ensure_active_profile(scene):
    profile = get_active_profile(scene)
    if profile is None:
        profile = create_profile(scene, "Default Render Profile")
    if not profile.snapshot_json:
        capture_snapshot(scene, profile)
    return profile


def get_profile_camera(scene, profile=None):
    profile = profile or get_active_profile(scene)
    if profile and profile.camera and profile.camera.type == "CAMERA":
        return profile.camera
    return scene.lod_props.lod_camera or scene.camera


def get_profile_objects(scene, profile=None):
    profile = profile or get_active_profile(scene)
    if profile and profile.scope_collection:
        return list(profile.scope_collection.all_objects)
    return list(scene.objects)


def capture_snapshot(scene, profile):
    objects = []
    for obj in _scene_objects(scene, profile):
        material_ids = []
        if obj.type == "MESH" and obj.data:
            for material in obj.data.materials:
                material_ids.append(_ensure_uuid(material) if material else "")
        modifiers = []
        for modifier in obj.modifiers:
            state = {
                "name": modifier.name,
                "type": modifier.type,
                "show_viewport": bool(modifier.show_viewport),
                "show_render": bool(modifier.show_render),
            }
            if modifier.type == "DECIMATE":
                state["ratio"] = float(modifier.ratio)
            elif modifier.type == "NODES":
                state["node_group"] = modifier.node_group.name if modifier.node_group else ""
                state["properties"] = {
                    key: _json_safe(modifier[key])
                    for key in modifier.keys()
                    if not key.startswith("_")
                }
            modifiers.append(state)

        objects.append(
            {
                "id": _ensure_uuid(obj),
                "name": obj.name,
                "mesh_id": _ensure_uuid(obj.data) if obj.type == "MESH" and obj.data else "",
                "display_type": getattr(obj, "display_type", "TEXTURED"),
                "hide_viewport": bool(obj.hide_viewport),
                "hide_render": bool(obj.hide_render),
                "color": list(getattr(obj, "color", (1.0, 1.0, 1.0, 1.0))),
                "material_ids": material_ids,
                "modifiers": modifiers,
            }
        )

    images = []
    for image in bpy.data.images:
        images.append(
            {
                "id": _ensure_uuid(image),
                "name": image.name,
                "filepath": image.filepath,
                "lod_original_path": image.get("lod_original_path"),
            }
        )

    collections = []
    for collection in bpy.data.collections:
        collections.append(
            {
                "id": _ensure_uuid(collection),
                "name": collection.name,
                "color_tag": getattr(collection, "color_tag", "NONE"),
            }
        )

    materials = []
    for material in bpy.data.materials:
        nodes = []
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                sockets = {}
                for socket_name in ("Strength", "Scale"):
                    socket = node.inputs.get(socket_name)
                    if socket and not socket.is_linked:
                        try:
                            sockets[socket_name] = float(socket.default_value)
                        except (TypeError, ValueError):
                            pass
                if sockets:
                    nodes.append({"name": node.name, "values": sockets})
        if nodes:
            materials.append({"id": _ensure_uuid(material), "nodes": nodes})

    snapshot = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "objects": objects,
        "images": images,
        "collections": collections,
        "materials": materials,
    }
    serialized = json.dumps(snapshot, ensure_ascii=True, separators=(",", ":"))
    # Keep the small property useful for diagnostics, but store the full snapshot
    # in a Text datablock so large production scenes are not truncated.
    profile.snapshot_json = serialized if len(serialized) <= 60000 else ""
    text_name = profile.snapshot_text_name or f"LODify_Profile_{profile.profile_id}"
    text_block = bpy.data.texts.get(text_name) or bpy.data.texts.new(text_name)
    text_block.clear()
    text_block.write(serialized)
    profile.snapshot_text_name = text_block.name
    profile.status = "CAPTURED"
    profile.last_report = f"Captured {len(objects)} objects and {len(images)} images."
    return snapshot


def _restore_material_slots(obj, material_ids):
    if obj.type != "MESH" or not obj.data:
        return
    materials = [
        _find_by_uuid(bpy.data.materials, material_id) if material_id else None
        for material_id in material_ids
    ]
    try:
        obj.data.materials.clear()
        for material in materials:
            if material:
                obj.data.materials.append(material)
            else:
                obj.data.materials.append(None)
    except Exception:
        # Some linked mesh datablocks are read-only; restore what is writable.
        for index, material in enumerate(materials):
            if index < len(obj.material_slots):
                try:
                    obj.material_slots[index].material = material
                except Exception:
                    pass


def restore_snapshot(scene, profile):
    snapshot_source = profile.snapshot_json
    if profile.snapshot_text_name:
        text_block = bpy.data.texts.get(profile.snapshot_text_name)
        if text_block:
            snapshot_source = text_block.as_string()
    if not snapshot_source:
        raise RuntimeError("This profile has no captured snapshot.")
    snapshot = json.loads(snapshot_source)

    restored_objects = 0
    for state in snapshot.get("objects", []):
        obj = _find_by_uuid(bpy.data.objects, state.get("id", ""))
        if not obj:
            continue
        try:
            mesh = _find_by_uuid(bpy.data.meshes, state.get("mesh_id", ""))
            if mesh and obj.type == "MESH" and obj.data != mesh:
                obj.data = mesh
        except Exception:
            pass
        try:
            obj.display_type = state.get("display_type", obj.display_type)
            obj.hide_viewport = bool(state.get("hide_viewport", obj.hide_viewport))
            obj.hide_render = bool(state.get("hide_render", obj.hide_render))
            if hasattr(obj, "color") and state.get("color"):
                obj.color = tuple(state["color"])
            _restore_material_slots(obj, state.get("material_ids", []))
            saved_modifiers = {item.get("name"): item for item in state.get("modifiers", [])}
            for modifier in list(obj.modifiers):
                owned_by_profile = modifier.get(GENERATED_PROFILE_KEY) == profile.profile_id
                legacy_owned = modifier.get(GENERATED_PROFILE_KEY) is None and obj.get("_lod_geo_lod_created")
                if (owned_by_profile or legacy_owned) and modifier.name not in saved_modifiers:
                    try:
                        obj.modifiers.remove(modifier)
                    except Exception:
                        pass
            for modifier in obj.modifiers:
                modifier_state = saved_modifiers.get(modifier.name)
                if not modifier_state:
                    continue
                try:
                    modifier.show_viewport = modifier_state.get("show_viewport", modifier.show_viewport)
                    modifier.show_render = modifier_state.get("show_render", modifier.show_render)
                    if modifier.type == "DECIMATE" and "ratio" in modifier_state:
                        modifier.ratio = modifier_state["ratio"]
                    elif modifier.type == "NODES":
                        for key, value in modifier_state.get("properties", {}).items():
                            modifier[key] = value
                except Exception:
                    pass
            restored_objects += 1
        except Exception:
            continue

    restored_images = 0
    for state in snapshot.get("images", []):
        image = _find_by_uuid(bpy.data.images, state.get("id", ""))
        if not image:
            continue
        try:
            image.filepath = state.get("filepath", "")
            original = state.get("lod_original_path")
            if original is None:
                if "lod_original_path" in image:
                    del image["lod_original_path"]
            else:
                image["lod_original_path"] = original
            if image.filepath:
                image.reload()
            restored_images += 1
        except Exception:
            continue

    restored_collections = 0
    for state in snapshot.get("collections", []):
        collection = _find_by_uuid(bpy.data.collections, state.get("id", ""))
        if not collection:
            continue
        try:
            collection.color_tag = state.get("color_tag", collection.color_tag)
            if collection.name != state.get("name") and " | " in collection.name:
                collection.name = state["name"]
            restored_collections += 1
        except Exception:
            continue

    restored_material_nodes = 0
    for state in snapshot.get("materials", []):
        material = _find_by_uuid(bpy.data.materials, state.get("id", ""))
        if not material or not material.use_nodes or not material.node_tree:
            continue
        for node_state in state.get("nodes", []):
            node = material.node_tree.nodes.get(node_state.get("name", ""))
            if not node:
                continue
            for socket_name, value in node_state.get("values", {}).items():
                socket = node.inputs.get(socket_name)
                if socket and not socket.is_linked:
                    try:
                        socket.default_value = value
                        restored_material_nodes += 1
                    except Exception:
                        pass
    # Generated material copies are safe to discard after original slots are restored.
    removed_materials = 0
    for material in list(bpy.data.materials):
        if material.get(GENERATED_PROFILE_KEY) == profile.profile_id and material.users == 0:
            try:
                bpy.data.materials.remove(material)
                removed_materials += 1
            except Exception:
                pass

    removed_meshes = 0
    for mesh in list(bpy.data.meshes):
        if mesh.get(GENERATED_PROFILE_KEY) == profile.profile_id and mesh.users == 0:
            try:
                bpy.data.meshes.remove(mesh)
                removed_meshes += 1
            except Exception:
                pass

    profile.status = "RESTORED"
    profile.last_report = (
        f"Restored {restored_objects} objects, {restored_images} images, "
        f"{restored_collections} collections, {restored_material_nodes} material values; "
        f"removed {removed_materials} materials and {removed_meshes} generated meshes."
    )
    return profile.last_report


def restore_material_assignments(profile):
    """Restore only object material slots for a profile-owned shader preview."""
    if not profile or not (profile.snapshot_json or profile.snapshot_text_name):
        raise RuntimeError("This profile has no captured snapshot.")
    snapshot_source = profile.snapshot_json
    if profile.snapshot_text_name:
        text_block = bpy.data.texts.get(profile.snapshot_text_name)
        if text_block:
            snapshot_source = text_block.as_string()
    snapshot = json.loads(snapshot_source)
    restored = 0
    for state in snapshot.get("objects", []):
        obj = _find_by_uuid(bpy.data.objects, state.get("id", ""))
        if not obj:
            continue
        _restore_material_slots(obj, state.get("material_ids", []))
        restored += 1
    removed = 0
    for material in list(bpy.data.materials):
        if material.get(GENERATED_PROFILE_KEY) == profile.profile_id and material.users == 0:
            try:
                bpy.data.materials.remove(material)
                removed += 1
            except Exception:
                pass
    return f"Restored materials on {restored} objects; removed {removed} generated variants."


class LODIFY_OT_ProfileCreate(bpy.types.Operator):
    bl_idname = "lodify.profile_create"
    bl_label = "New Render Profile"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = create_profile(context.scene)
        capture_snapshot(context.scene, profile)
        self.report({"INFO"}, f"Created profile: {profile.name}")
        return {"FINISHED"}


class LODIFY_OT_ProfileCapture(bpy.types.Operator):
    bl_idname = "lodify.profile_capture"
    bl_label = "Capture Original State"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = get_active_profile(context.scene) or create_profile(context.scene)
        capture_snapshot(context.scene, profile)
        self.report({"INFO"}, profile.last_report)
        return {"FINISHED"}


class LODIFY_OT_ProfileRestore(bpy.types.Operator):
    bl_idname = "lodify.profile_restore"
    bl_label = "Restore Profile"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        profile = get_active_profile(context.scene)
        if not profile:
            self.report({"WARNING"}, "Create a profile first.")
            return {"CANCELLED"}
        try:
            message = restore_snapshot(context.scene, profile)
        except Exception as exc:
            profile.status = "ERROR"
            profile.last_report = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}


classes = (
    LODIFY_Profile,
    LODIFY_UL_Profiles,
    LODIFY_OT_ProfileCreate,
    LODIFY_OT_ProfileCapture,
    LODIFY_OT_ProfileRestore,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lodify_profiles = CollectionProperty(type=LODIFY_Profile)
    bpy.types.Scene.lodify_active_profile = IntProperty(default=0, min=0)


def unregister():
    if hasattr(bpy.types.Scene, "lodify_active_profile"):
        del bpy.types.Scene.lodify_active_profile
    if hasattr(bpy.types.Scene, "lodify_profiles"):
        del bpy.types.Scene.lodify_profiles
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
