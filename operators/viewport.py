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
        
        # --- 定义显示模式的权重 (数字越小越省资源) ---
        DISPLAY_RANKS = {
            'TEXTURED': 3,
            'SOLID':    2,
            'WIRE':     1,
            'BOUNDS':   0
        }

        # 3. 遍历场景物体
        for obj in context.scene.objects:
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue

            # --- [快照逻辑] 保存原始状态 ---
            if "_tot_orig_display" not in obj:
                obj["_tot_orig_display"] = obj.display_type
            
            if "_tot_orig_hide" not in obj:
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
            
            # 获取 LOD 建议的目标模式
            attr_name = f"view_lod{level}_display"
            target_display = getattr(scn, attr_name, 'BOUNDS')
            
            # --- [核心修改] 降级保护逻辑 ---
            # 1. 获取该物体最原始的显示模式
            orig_display = obj.get("_tot_orig_display", 'TEXTURED')
            
            # 2. 比较权重
            rank_target = DISPLAY_RANKS.get(target_display, 2)
            rank_orig   = DISPLAY_RANKS.get(orig_display, 2)
            
            # 3. 取较小值 (min)：如果 LOD 建议是 Solid(2)，但原物是 Wire(1)，则保持 Wire
            if rank_target < rank_orig:
                final_display = target_display
            else:
                final_display = orig_display
                
            # --- [额外优化] 隐藏状态保护 ---
            # 如果物体原本就是隐藏的，也不要因为 LOD 而把它显示出来
            should_hide_by_lod = (level == 3 and scn.view_lod3_hide)
            orig_is_hidden = bool(obj.get("_tot_orig_hide", 0))
            
            # 应用属性
            obj.display_type = final_display
            obj.hide_viewport = should_hide_by_lod or orig_is_hidden
            
            count += 1
            
        self.report({'INFO'}, f"Viewport LOD Updated: {count} objects processed (Downgrade Only).")
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