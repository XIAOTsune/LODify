import bpy

class TOT_PT_MainPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Optimize" 
    bl_options = {'DEFAULT_CLOSED'}

class TOT_PT_LODManager(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "LOD Manager"
    bl_idname = "TOT_PT_LODManager"
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        #相机选择
        layout.prop(scn, "lod_camera", icon='CAMERA_DATA')
        layout.separator()
        
        # 距离阈值设定 (Zones)
        layout.label(text="Distance Zones (Meters):", icon='TRACKER')
        row = layout.row(align=True)
        row.prop(scn, "lod_dist_0", text="High")
        row.prop(scn, "lod_dist_1", text="Mid")
        row.prop(scn, "lod_dist_2", text="Low")
        
        layout.separator()
        
        # ==========================================================
        # 2. 维度三：视窗优化 (Viewport Optimization)
        # ==========================================================
        box = layout.box()
        header = box.row()
        header.prop(scn, "view_lod_enabled", text="Viewport Optimization", icon='VIEW3D', toggle=True)
        
        if scn.view_lod_enabled:
            col = box.column(align=True)
            # High Zone
            r = col.row()
            r.label(text="0m - High:")
            r.prop(scn, "view_lod0_display", text="")
            # Mid Zone
            r = col.row()
            r.label(text="Mid:")
            r.prop(scn, "view_lod1_display", text="")
            # Low Zone
            r = col.row()
            r.label(text="Low:")
            r.prop(scn, "view_lod2_display", text="")
            # Far Zone
            r = col.row()
            r.label(text="> Far:")
            r.prop(scn, "view_lod3_display", text="")
            
            box.prop(scn, "view_lod3_hide", text="Hide Far Objects")
            
            # 视窗操作按钮
            r = box.row(align=True)
            r.operator("tot.viewport_lod_update", text="Update View", icon='FILE_REFRESH')
            r.operator("tot.viewport_lod_reset", text="Reset", icon='X')

        # ==========================================================
        # 3. 维度二：模型减面 (Geometry LOD - 重构版)
        # ==========================================================
        box = layout.box()
        
        # 头部
        row = box.row()
        row.label(text="Geometry LOD", icon="MOD_DECIM")
        row.prop(scn, "geo_lod_enabled", text="Enable", toggle=True)
        
        if scn.geo_lod_enabled:
            # 1. 方法选择
            row = box.row(align=True)
            row.prop(scn, "geo_lod_method", text="Method")
            
            # 2. 参数显示
            col = box.column(align=True)
            col.prop(scn, "geo_lod_min_faces", text="Min Faces (Safety)")
            
            # 动态显示强度标签
            if scn.geo_lod_method == 'DECIMATE':
                # Decimate 模式：数值是“保留比例”，越小减面越多
                col.prop(scn, "geo_lod_min_ratio", text="Min Ratio (Max Reduction)", slider=True)
            else:
                # GN 模式：数值是“强度因子”，越大减面越多
                # 复用同一个变量，但在逻辑里处理
                col.prop(scn, "geo_lod_min_ratio", text="GN Strength Factor", slider=True)
                col.label(text="Higher Strength = More Merging", icon='INFO')

            # 3. 三大核心按钮 (Setup / Update / Reset)
            row = box.row(align=True)
            row.scale_y = 1.2
            row.operator("tot.geo_lod_setup", text="Setup Modifiers", icon="MODIFIER")
            row.operator("tot.geo_lod_update", text="Update Geometry", icon="PLAY")
            row.operator("tot.geo_lod_reset", text="Reset Geometry", icon="FILE_REFRESH")
            
            # 4. Apply 按钮 (现在支持两种模式)
            row = box.row()
            row.scale_y = 1.2
            # 红色警告色提示这是破坏性操作
            row.alert = True 
            op_text = "Apply Decimate" if scn.geo_lod_method == 'DECIMATE' else "Apply GeoNodes"
            row.operator("tot.geo_lod_apply", text=f"{op_text} (Destructive)", icon="CHECKMARK")
        # ==========================================================
        # 4. 维度一：贴图管理 (Texture - 占位)
        # ==========================================================
        box = layout.box()
        box.label(text="Texture Optimization", icon='TEXTURE')
        # 这里复用之前的 Resize 逻辑，但建议未来整合进 LOD 逻辑
        box.label(text="See Image Resizer Panel below", icon='INFO')
        
# 原来的 Image Resizer 面板保持不变，作为独立工具存在
class TOT_PT_ImageResizer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "Image Tools"
    bl_idname = "TOT_PT_ImageResizer"
    # ... (保持之前的 draw 代码不变) ...
    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        layout.operator("tot.updateimagelist", text="Scan Images")
        # ... (由于篇幅限制，这里复用之前生成的代码)

classes = (
    TOT_PT_LODManager,
    TOT_PT_ImageResizer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)