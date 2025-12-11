import bpy
from mathutils import Vector

class TOT_OT_ViewportLODUpdate(bpy.types.Operator):
    """根据距离更新视窗显示模式 (Solid/Wire/Bounds)"""
    bl_idname = "tot.viewport_lod_update"
    bl_label = "Update Viewport LOD"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene.tot_props
        
        if not scn.view_lod_enabled:
            self.report({'WARNING'}, "Viewport LOD is disabled in settings.")
            return {'CANCELLED'}

        # 1. 确定相机
        cam = scn.lod_camera or context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No Camera found for LOD calculation.")
            return {'CANCELLED'}
        
        cam_loc = cam.matrix_world.translation
        d0, d1, d2 = scn.lod_dist_0, scn.lod_dist_1, scn.lod_dist_2
        
        count = 0
        
        # 3. 遍历场景物体
        for obj in context.scene.objects:
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue

            # --- [核心修改] 第一次运行时，保存原始状态 ---
            # 我们使用自定义属性 (Custom Properties) 存储，不会影响渲染，且随文件保存
            if "_tot_orig_display" not in obj:
                obj["_tot_orig_display"] = obj.display_type
            
            if "_tot_orig_hide" not in obj:
                # 记录原始的隐藏状态 (注意：int 0/1 转换)
                obj["_tot_orig_hide"] = int(obj.hide_viewport)
            # -----------------------------------------------

            # 计算距离
            try:
                bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                center = sum(bbox_world, Vector()) / 8.0
            except:
                center = obj.matrix_world.translation
            
            dist = (center - cam_loc).length
            
            # 判定 Level
            level = 0
            if dist <= d0: level = 0
            elif dist <= d1: level = 1
            elif dist <= d2: level = 2
            else: level = 3
            
            # 获取设置并应用
            attr_name = f"view_lod{level}_display"
            display_type = getattr(scn, attr_name, 'BOUNDS')
            should_hide = (level == 3 and scn.view_lod3_hide)
            
            obj.display_type = display_type
            obj.hide_viewport = should_hide
            
            count += 1
            
        self.report({'INFO'}, f"Viewport LOD Updated: {count} objects processed.")
        return {'FINISHED'}

class TOT_OT_ViewportLODReset(bpy.types.Operator):
    """恢复物体原本的显示模式"""
    bl_idname = "tot.viewport_lod_reset"
    bl_label = "Reset Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restored_count = 0
        default_count = 0
        
        for obj in context.scene.objects:
            # 只处理几何体
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue
                
            # --- [核心修改] 优先尝试从快照恢复 ---
            if "_tot_orig_display" in obj:
                # 恢复显示模式 (SOLID, WIRE, etc.)
                # 有时候保存的是 int，有时候是 str，根据 blender 版本稍微容错一下
                try:
                    obj.display_type = obj["_tot_orig_display"]
                except:
                    # 万一出错，回退到 Textured
                    obj.display_type = 'TEXTURED'
                
                # 恢复完成，删除快照，以便下次重新Update时记录新状态
                del obj["_tot_orig_display"]
                restored_count += 1
            else:
                # 如果没有快照 (比如手动操作过的物体)，默认回退到 Textured
                obj.display_type = 'TEXTURED'
                default_count += 1
            
            if "_tot_orig_hide" in obj:
                # 恢复隐藏状态
                obj.hide_viewport = bool(obj["_tot_orig_hide"])
                del obj["_tot_orig_hide"]
            else:
                # 默认显示
                obj.hide_viewport = False
            # ---------------------------------------
        
        msg = f"Reset: Restored {restored_count} objects to original state"
        if default_count > 0:
            msg += f", reset {default_count} to default."
            
        self.report({'INFO'}, msg)
        return {'FINISHED'}

classes = (
    TOT_OT_ViewportLODUpdate,
    TOT_OT_ViewportLODReset,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)