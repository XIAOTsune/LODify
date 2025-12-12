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
                
            # --- [核心修改] 即使恢复了也不删除快照，允许反复重置 ---
            if "_tot_orig_display" in obj:
                try:
                    # 总是从快照中读取状态
                    obj.display_type = obj["_tot_orig_display"]
                except:
                    obj.display_type = 'TEXTURED'
                
                # [关键改动] 注释掉删除逻辑，确保持久记忆
                # del obj["_tot_orig_display"] 
                restored_count += 1
            else:
                # 如果从来没有记录过（即未参与过优化），才使用默认值
                # 这里也可以选择什么都不做，保持现状
                # obj.display_type = 'TEXTURED' 
                pass # 建议改为 pass，防止误伤未处理的物体
            
            if "_tot_orig_hide" in obj:
                obj.hide_viewport = bool(obj["_tot_orig_hide"])
                # [关键改动] 注释掉删除逻辑
                # del obj["_tot_orig_hide"]
            else:
                obj.hide_viewport = False
            # ---------------------------------------
        
        self.report({'INFO'}, f"Reset Viewport: Restored {restored_count} objects.")
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