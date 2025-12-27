# File Path: .\ui\main_panels.py

import bpy
import os
from .. import AUTHOR_NAME
from ..i18n import i18n

# 移除了旧的 _(msg) 函数，统一使用导入的 i18n()

class LOD_PT_MainPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Optimize" 
    bl_options = {'DEFAULT_CLOSED'}


class LOD_PT_Header(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "" 
    bl_idname = "LOD_PT_Header"
    bl_order = 0
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.scale_y = 1.2
        # 翻译: LODify
        row.label(text=i18n("LODify"), icon='MODIFIER')
        layout.separator()

class LOD_PT_CollectionAnalyzer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "1. Collection Analyzer"
    bl_idname = "LOD_PT_CollectionAnalyzer"
    bl_order = 1

    def draw_header(self, context):
        # 翻译: 集合分析器
        self.layout.label(text=i18n("Collection Analyzer"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        # 翻译: 算法/方法
        layout.prop(scn, "colA_Method", text=i18n("Method"))
        
        if scn.colA_Method == 'm2':
            box = layout.box()
            # 翻译: 颜色阈值 (顶点百分比)
            box.label(text=i18n("Color Thresholds (Vertex %)"), icon='PREFERENCES')
            col = box.column(align=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_01'); r.prop(scn, "mult_veryhigh", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_02'); r.prop(scn, "mult_high", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_03'); r.prop(scn, "mult_medium", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_04'); r.prop(scn, "mult_low", slider=True)
            r = col.row(); r.label(text="", icon='COLLECTION_COLOR_05'); r.prop(scn, "mult_very_low", slider=True)

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.2
        
        if not scn.CA_Toggle:
            # 翻译: 运行分析
            row.operator("lod.collectionanalyzer", text=i18n("Run Analyzer"), icon='PLAY')
        else:
            # 翻译: 清除结果
            row.operator("lod.cleancolors", text=i18n("Clear Analyzer"), icon='X')
            row.operator("lod.collectionanalyzer", text="", icon='FILE_REFRESH')

class LOD_PT_ViewAnalyzer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "2. View Analyzer"
    bl_idname = "LOD_PT_ViewAnalyzer"
    bl_order = 2

    def draw_header(self, context):
        # 翻译: 视图分析器
        self.layout.label(text=i18n("View Analyzer"))
        
    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        # 翻译: 视图分析器
        layout.label(text=i18n("View Analyzer"), icon='SCENE_DATA')
        row = layout.row(align=True)
        row.scale_y = 1.2
        if not scn.AA_Toggle:
            # 翻译: 运行视图分析
            row.operator("lod.viewanalyzer", text=i18n("Run 3D View Analyzer"), icon='PLAY')
        else:
            # 翻译: 清除视图分析
            row.operator("lod.cleanviewanalyzer", text=i18n("Clear View Analyzer"), icon='X')

class LOD_PT_ImageResizer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "3. Image Resizer"
    bl_idname = "LOD_PT_ImageResizer"
    bl_order = 3

    def draw_header(self, context):
        # 翻译: 贴图缩放管理
        self.layout.label(text=i18n("Image Resizer"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        row = layout.row()
        row.scale_y = 1.2
        # 翻译: 扫描 / 刷新图片列表
        row.operator("lod.updateimagelist", text=i18n("Scan / Refresh Images"), icon='FILE_REFRESH')
        
        if scn.r_total_images > 0:
            box = layout.box()
            r = box.row()
            # 翻译: 总计, 显存
            r.label(text=f"{i18n('Total')}: {scn.r_total_images}")
            r.label(text=f"{i18n('Mem')}: {scn.total_image_memory} MB")
        
        layout.template_list("LOD_UL_ImageStats", "", scn, "image_list", scn, "custom_index_image_list", rows=5)
        
        row = layout.row(align=True)
        # 翻译: 全选 / 反选
        row.operator("lod.imglistselectall", text=i18n("Select All/None"), icon='CHECKBOX_HLT')
        
        layout.separator()
        # 翻译: 缩放选项:
        layout.label(text=i18n("Resize Options:"), icon='TOOL_SETTINGS')
        
        col = layout.column(align=True)
        # 翻译: 目标
        col.prop(scn, "resize_size", text=i18n("Target Size"))
        if scn.resize_size == 'c':
            # 翻译: 像素
            col.prop(scn, "custom_resize_size", text=i18n("Pixels"))
            
        # 翻译: 安全模式 (另存副本)
        col.prop(scn, "duplicate_images", text=i18n("Safe Mode (Copy Files)"))
        if scn.duplicate_images and not scn.use_same_directory:
             # 翻译: 输出
             col.prop(scn, "custom_output_path", text=i18n("Output"))
             
        row = layout.row()
        row.scale_y = 1.4
        # 翻译: 缩放选中图片
        row.operator("lod.resizeimages_async", text=i18n("Resize Selected Images"), icon='IMAGE_DATA')

        layout.separator()
        box_cam = layout.box()
        # 翻译: AI / 相机视角优化
        box_cam.label(text=i18n("AI / Camera Optimization"), icon='VIEW_CAMERA')
        col = box_cam.column(align=True)
        # 翻译: 基于屏幕占比自动计算尺寸
        col.label(text=i18n("Auto-calculate size based on screen coverage"), icon='INFO')
        # 翻译: 运行相机优化
        col.operator("lod.optimize_by_camera", text=i18n("Run Camera Optimization"), icon='SHADING_RENDERED')

        layout.separator()
        box = layout.box()
        # 翻译: 全局贴图切换
        box.label(text=i18n("Texture Switcher (Global)"), icon='UV_SYNC_SELECT')
        
        row = box.row(align=True)
        row.scale_y = 1.2
        
        # 翻译: 原图
        op = row.operator("lod.switch_resolution", text=i18n("Original"), icon='FILE_IMAGE')
        op.target_res = "ORIGINAL"
        
        base_path = bpy.path.abspath("//")
        if base_path and os.path.exists(os.path.join(base_path, "textures_camera_optimized")):
            # 翻译: 自动
            op = row.operator("lod.switch_resolution", text=i18n("Auto-Opt"), icon='CAMERA_DATA')
            op.target_res = "camera_optimized"

        found_resolutions = []
        if base_path and os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    if os.path.isdir(os.path.join(base_path, item)) and item.startswith("textures_") and item.endswith("px"):
                        res_str = item.replace("textures_", "").replace("px", "")
                        if res_str.isdigit():
                            found_resolutions.append(res_str)
            except: pass
        found_resolutions.sort(key=int)
        
        if found_resolutions:
            for res in found_resolutions:
                op = row.operator("lod.switch_resolution", text=f"{res}px")
                op.target_res = res
        else:
            # 翻译: (未找到已生成的尺寸组)
            row.label(text=i18n("(No resized sets found)"))

class LOD_PT_LODManager(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "4. LOD Manager"
    bl_idname = "LOD_PT_LODManager"
    bl_order = 4

    def draw_header(self, context):
        # 翻译: LOD 层级管理
        self.layout.label(text=i18n("LOD Manager"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        # 翻译: LOD 计算相机
        layout.prop(scn, "lod_camera", text=i18n("LOD Camera"), icon='CAMERA_DATA')
        layout.separator()
        
        col = layout.column(align=True)
        # 翻译: LOD 距离分级 (仅影响视窗)
        col.label(text=i18n("LOD Distance Levels (For Viewport)"), icon='DRIVER_DISTANCE')
        
        row = col.row(align=True)
        # 翻译: 高精度 <, 中精度 <, 低精度 <
        row.prop(scn, "lod_dist_0", text=i18n("High <"))
        row.prop(scn, "lod_dist_1", text=i18n("Mid <"))
        row.prop(scn, "lod_dist_2", text=i18n("Low <"))
        
        layout.separator()

        box = layout.box()
        header = box.row()
        # 翻译: 视窗显示优化
        header.prop(scn, "view_lod_enabled", text=i18n("Viewport Optimization"), icon='VIEW3D', toggle=True)
        
        if scn.view_lod_enabled:
            col = box.column(align=True)
            def draw_lod_row(layout, label, prop_name):
                row = layout.row(align=True)
                row.label(text=label)
                row.prop(scn, prop_name, text="")
            
            # 注意这里使用了 f-string 和 i18n 混合
            draw_lod_row(col, f"0m - {scn.lod_dist_0}m ({i18n('High <')}):", "view_lod0_display")
            draw_lod_row(col, f"{scn.lod_dist_0}m - {scn.lod_dist_1}m ({i18n('Mid <')}):", "view_lod1_display")
            draw_lod_row(col, f"{scn.lod_dist_1}m - {scn.lod_dist_2}m ({i18n('Low <')}):", "view_lod2_display")
            draw_lod_row(col, f"> {scn.lod_dist_2}m (Far):", "view_lod3_display")
            
            col.separator()
            # 翻译: 隐藏极远物体
            col.prop(scn, "view_lod3_hide", text=i18n("Hide Far Objects"))
            
            r = box.row(align=True)
            r.scale_y = 1.2
            # 翻译: 更新视图
            r.operator("lod.viewport_lod_update", text=i18n("Update View"), icon='FILE_REFRESH')
            # 翻译: 重置
            r.operator("lod.viewport_lod_reset", text=i18n("Reset"), icon='X')

        layout.separator()
        box = layout.box()
        
        row = box.row()
        # 翻译: 几何体 LOD (屏幕占比模式)
        row.label(text=i18n("Geometry LOD (Screen Ratio)"), icon="MOD_DECIM")
        # 翻译: 启用
        row.prop(scn, "geo_lod_enabled", text=i18n("Enable"), toggle=True)
        
        if scn.geo_lod_enabled:
            row = box.row(align=True)
            # 翻译: 算法/方法
            row.prop(scn, "geo_lod_method", text=i18n("Method"))
            
            col = box.column(align=True)
            # 翻译: 最小面数保护
            col.prop(scn, "geo_lod_min_faces", text=i18n("Min Faces (Safety)"))
            
            if scn.geo_lod_method == 'DECIMATE':
                # 翻译: 最小比例保护
                col.prop(scn, "geo_lod_min_ratio", text=i18n("Min Ratio (Safety Floor)"), slider=True)
                # 翻译: 防止近景或特写时的细节丢失
                col.label(text=i18n("Prevents breaking close-up details"), icon='INFO')
            else:
                # 翻译: 节点强度因子
                col.prop(scn, "geo_lod_min_ratio", text=i18n("GN Strength Factor"), slider=True)
                row = col.row(align=True)
                # 翻译: 最大合并距离
                row.prop(scn, "geo_lod_max_dist", text=i18n("Max Merge Distance"))
                row.label(text="", icon='DRIVER_DISTANCE')
                
                box_in = col.box()
                # 翻译: 自动边缘保护 (智能)
                box_in.label(text=i18n("Auto Edge Protection"), icon='SHADING_WIRE')
                # 翻译: 基于距离的空间塌陷
                box_in.label(text=i18n("Distance-based Collapse"), icon='MOD_PARTICLES')
            
            row = box.row(align=True)
            row.scale_y = 1.2
            # 翻译: 安装修改器
            row.operator("lod.geo_lod_setup", text=i18n("Setup Modifiers"), icon="MODIFIER")
            # 翻译: 更新模型 (异步)
            row.operator("lod.geo_lod_update_async", text=i18n("Update Geometry (Async)"), icon="PLAY")
            # 翻译: 重置模型
            row.operator("lod.geo_lod_reset", text=i18n("Reset Geometry",), icon="FILE_REFRESH")   
            
            row = box.row()
            row.scale_y = 1.2
            row.alert = True 
            # 翻译: 应用减面 (不可逆) / 应用几何节点 (不可逆)
            op_text = i18n("Apply Decimate (Destructive)") if scn.geo_lod_method == 'DECIMATE' else i18n("Apply GeoNodes (Destructive)")
            row.operator("lod.geo_lod_apply_async", text=op_text, icon="CHECKMARK")

class LOD_PT_DuplicateRemover(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "5. Clean Up & Storage"
    bl_idname = "LOD_PT_DuplicateRemover"
    bl_order = 5
    
    def draw_header(self, context):
        # 翻译: 清理与存储
        self.layout.label(text=i18n("Clean Up & Storage"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        box = layout.box()
        # 翻译: 数据清理
        box.label(text=i18n("Data Cleanup"), icon='BRUSH_DATA')
        col = box.column(align=True)
        # 翻译: 合并重复贴图 (.001)
        col.operator("lod.clearduplicateimage", text=i18n("Merge Duplicate Images (.001)"), icon='TRASH')

        box = layout.box()
        # 翻译: 磁盘存储管理
        box.label(text=i18n("Disk Storage Management"), icon='FILE_FOLDER')
        
        raw_path = bpy.path.abspath("//")
        base_path = os.path.normpath(raw_path) if raw_path else None
        
        if not base_path or not os.path.exists(base_path):
            # 翻译: 保存文件后可见贴图文件夹
            box.label(text=i18n("Save file to see texture folders"), icon='ERROR')
        else:
            texture_folders = []
            try:
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path) and item.startswith("textures_"):
                        texture_folders.append(item)
            except Exception as e:
                box.label(text=f"Scan Error: {str(e)}", icon='ERROR')
            
            if not texture_folders:
                # 翻译: 未找到已生成的贴图文件夹。
                box.label(text=i18n("No generated folders found."), icon='INFO')
            else:
                # 翻译: 发现 X 组贴图缓存
                box.label(text=f"{i18n('Found')} {len(texture_folders)} {i18n('Texture Sets')}:", icon='FILE_IMAGE')
                for folder in texture_folders:
                    row = box.row()
                    row.alignment = 'EXPAND'
                    row.label(text=folder, icon='FOLDER_REDIRECT')
                    op = row.operator("lod.delete_texture_folder", text="", icon='X')
                    op.folder_name = folder

class LOD_PT_Experimental(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "6. Experimental Features"
    bl_idname = "LOD_PT_Experimental"
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        # 翻译: 实验性功能
        self.layout.label(text=i18n("Experimental Features"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        box_lod = layout.box()
        row = box_lod.row()
        # 翻译: 材质细节 LOD
        row.label(text=i18n("Shader Detail LOD"), icon='SHADING_RENDERED')
        # 翻译: 启用
        row.prop(scn, "exp_shader_lod_enabled", text=i18n("Enable"), toggle=True)
        
        if scn.exp_shader_lod_enabled:
            col = box_lod.column(align=True)
            # 翻译: 法线强度倍率
            col.label(text=i18n("Normal Map Strength Multipliers"), icon='NODE_MATERIAL')
            def draw_mult_row(layout, label, prop_name):
                row = layout.row(align=True)
                row.label(text=label); row.prop(scn, prop_name, text="")
            
            # 使用 i18n 翻译 'Mid <' 等
            draw_mult_row(col, f"LOD 1 ({i18n('Mid <')}):", "exp_normal_mult_1")
            draw_mult_row(col, f"LOD 2 ({i18n('Low <')}):", "exp_normal_mult_2")
            draw_mult_row(col, f"LOD 3 (Far):", "exp_normal_mult_3")
            col.separator()
            # 翻译: 置换强度倍率
            col.label(text=i18n("Displacement Scale Multipliers"), icon='MOD_DISPLACE')
            draw_mult_row(col, f"LOD 1 ({i18n('Mid <')}):", "exp_disp_mult_1")
            draw_mult_row(col, f"LOD 2 ({i18n('Low <')}):", "exp_disp_mult_2")
            draw_mult_row(col, f"LOD 3 (Far):", "exp_disp_mult_3")
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.2
            # 翻译: 更新材质
            row.operator("lod.shader_lod_update_async", text=i18n("Update Shaders"), icon='PLAY')
            # 翻译: 重置
            row.operator("lod.shader_lod_reset", text=i18n("Reset"), icon='LOOP_BACK')
classs = (
    LOD_PT_Header,
    LOD_PT_CollectionAnalyzer,
    LOD_PT_ViewAnalyzer,
    LOD_PT_ImageResizer,
    LOD_PT_LODManager,
    LOD_PT_DuplicateRemover,
    LOD_PT_Experimental,
)

def register():
    for cls in classs:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classs):
        bpy.utils.unregister_class(cls)