import bpy

class TOT_PT_MainPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Optimize" 
    bl_options = {'DEFAULT_CLOSED'}

# 1. 集合分析器 (Collection Analyzer)
class TOT_PT_CollectionAnalyzer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "1. Collection Analyzer"
    bl_idname = "TOT_PT_CollectionAnalyzer"
    bl_order = 1 # 排序权重

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        layout.prop(scn, "colA_Method", text="Method")
        
        # 如果是高级模式，显示颜色阈值
        if scn.colA_Method == 'm2':
            box = layout.box()
            box.label(text="Color Thresholds (Vertex %):", icon='PREFERENCES')
            
            col = box.column(align=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_01'); r.prop(scn, "mult_veryhigh", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_02'); r.prop(scn, "mult_high", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_03'); r.prop(scn, "mult_medium", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_04'); r.prop(scn, "mult_low", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_05'); r.prop(scn, "mult_very_low", slider=True)

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.2
        
        # Toggle 按钮逻辑
        if not scn.CA_Toggle:
            row.operator("tot.collectionanalyzer", text="Run Analyzer", icon='PLAY')
        else:
            row.operator("tot.cleancolors", text="Clear Analyzer", icon='X')
            row.operator("tot.collectionanalyzer", text="", icon='FILE_REFRESH') # 刷新按钮

# 2. 视图分析器 (View Analyzer)
class TOT_PT_ViewAnalyzer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "2. View Analyzer"
    bl_idname = "TOT_PT_ViewAnalyzer"
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        layout.label(text="Color Objects by Vert Count", icon='SCENE_DATA')
        
        row = layout.row(align=True)
        row.scale_y = 1.2
        if not scn.AA_Toggle:
            row.operator("tot.viewanalyzer", text="Run View Analyzer", icon='PLAY')
        else:
            row.operator("tot.cleanviewanalyzer", text="Clear View Analyzer", icon='X')

# 3. 贴图列表与缩放 (Image Resizer)
class TOT_PT_ImageResizer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "3. Image Resizer"
    bl_idname = "TOT_PT_ImageResizer"
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        # 扫描按钮
        row = layout.row()
        row.scale_y = 1.2
        row.operator("tot.updateimagelist", text="Scan / Refresh Images", icon='FILE_REFRESH')
        
        # 统计信息
        if scn.r_total_images > 0:
            box = layout.box()
            r = box.row()
            r.label(text=f"Total: {scn.r_total_images}")
            r.label(text=f"Mem: {scn.total_image_memory} MB")
        
        # 列表
        layout.template_list("TOT_UL_ImageStats", "", scn, "image_list", scn, "custom_index_image_list", rows=5)
        
        # 选择工具
        row = layout.row(align=True)
        row.operator("tot.imglistselectall", text="Select All/None", icon='CHECKBOX_HLT')
        
        layout.separator()
        layout.label(text="Resize Options:", icon='TOOL_SETTINGS')
        
        # 缩放选项
        col = layout.column(align=True)
        col.prop(scn, "resize_size", text="Target")
        if scn.resize_size == 'c':
            col.prop(scn, "custom_resize_size", text="Pixels")
            
        col.prop(scn, "duplicate_images", text="Safe Mode (Copy Files)")
        if scn.duplicate_images and not scn.use_same_directory:
             col.prop(scn, "custom_output_path", text="Output")
             
        # 执行缩放
        row = layout.row()
        row.scale_y = 1.4
        row.operator("tot.resizeimages", text="Resize Selected Images", icon='IMAGE_DATA')

# 4. LOD层级管理 (LOD Manager)
class TOT_PT_LODManager(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "LOD Manager"
    bl_idname = "TOT_PT_LODManager"
    bl_order = 4

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

# 5. 去除重复贴图 (Duplicate Remover)
class TOT_PT_DuplicateRemover(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "5. Clean Up"
    bl_idname = "TOT_PT_DuplicateRemover"
    bl_order = 5
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Remove Duplicates", icon='BRUSH_DATA')
        box.label(text="Merges Image.001 -> Image", icon='INFO')
        
        row = box.row()
        row.scale_y = 1.2
        row.operator("tot.clearduplicateimage", text="Remove Duplicate Images", icon='TRASH')        

classes = (
    TOT_PT_CollectionAnalyzer,
    TOT_PT_ViewAnalyzer,
    TOT_PT_ImageResizer,
    TOT_PT_LODManager,
    TOT_PT_DuplicateRemover
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)