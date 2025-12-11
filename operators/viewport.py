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
        
        # 2. 获取阈值
        d0 = scn.lod_dist_0
        d1 = scn.lod_dist_1
        d2 = scn.lod_dist_2
        
        count = 0
        
        # 3. 遍历场景物体 (可以优化为只遍历选中的，或者指定集合)
        for obj in context.scene.objects:
            # 只处理几何体
            if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
                continue
                
            # 计算距离 (使用包围盒中心，比原点更准)
            try:
                # 简单计算：取包围盒8个点的平均值作为中心
                bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                center = sum(bbox_world, Vector()) / 8.0
            except:
                center = obj.matrix_world.translation
            
            dist = (center - cam_loc).length
            
            # 4. 判定 Level
            level = 0
            if dist <= d0:
                level = 0
            elif dist <= d1:
                level = 1
            elif dist <= d2:
                level = 2
            else:
                level = 3
                
            # 5. 应用设置
            # 获取对应层级的显示设置属性名
            attr_name = f"view_lod{level}_display"
            display_type = getattr(scn, attr_name, 'BOUNDS')
            
            # 特殊处理：Level 3 是否隐藏
            should_hide = (level == 3 and scn.view_lod3_hide)
            
            # 写入状态
            obj.display_type = display_type
            obj.hide_viewport = should_hide
            
            count += 1
            
        self.report({'INFO'}, f"Viewport LOD Updated: {count} objects processed.")
        return {'FINISHED'}

class TOT_OT_ViewportLODReset(bpy.types.Operator):
    """重置所有物体为 Textured 显示"""
    bl_idname = "tot.viewport_lod_reset"
    bl_label = "Reset Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.scene.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                obj.display_type = 'TEXTURED'
                obj.hide_viewport = False
        
        self.report({'INFO'}, "Viewport display reset.")
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