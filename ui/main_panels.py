import bpy
import os
from ..i18n import tr
from .. import AUTHOR_NAME

class TOT_PT_MainPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Optimize" 
    bl_options = {'DEFAULT_CLOSED'}
#0. 顶部 Header与语言切换 面板
class TOT_PT_Header(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "" # 不显示默认标题，我们自己画
    bl_idname = "TOT_PT_Header"
    bl_order = 0  # 排序第一
    bl_options = {'HIDE_HEADER'} # 隐藏折叠箭头，看起来像纯 UI 栏

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props

        # 创建一行
        row = layout.row(align=True)
        row.scale_y = 1.2 # 稍微高一点
        
        # 左侧：插件标题
        # 根据语言切换标题
        title = "LODify" if scn.language == 'EN' else "Blender 优化工具"
        row.label(text=title, icon='MODIFIER')

        sub = row.row()
        sub.scale_x = 0.8 # 让字体或者间距稍微紧凑一点，视情况调整
        sub.alignment = 'RIGHT' # 靠右对齐一点，或者紧跟标题
        
        # 这里的 icon 可以选 'URL', 'WORLD', 'COMMUNITY', 'User' 等
        # text 显示你的名字
        op = row.operator("tot.open_website", text=AUTHOR_NAME, icon='COMMUNITY', emboss=False)
        
        # 右侧：语言切换按钮 (expand=True 会把 Enum 显示为按钮组)
        row.prop(scn, "language", expand=True)
        
        layout.separator()

# 1. 集合分析器 (Collection Analyzer)
class TOT_PT_CollectionAnalyzer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "1. Collection Analyzer"
    bl_idname = "TOT_PT_CollectionAnalyzer"
    bl_order = 1 # 排序权重

    #动态修改面板标题
    def draw_header(self, context):
        self.layout.label(text=tr("Collection Analyzer"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        layout.prop(scn, "colA_Method", text=tr("Method"))
        
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

    def draw_header(self, context):
        self.layout.label(text=tr("View Analyzer"))
        
    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        layout.label(text=tr("View Analyzer"), icon='SCENE_DATA')
        
        row = layout.row(align=True)
        row.scale_y = 1.2
        if not scn.AA_Toggle:
            row.operator("tot.viewanalyzer", text=tr("Run Analyzer"), icon='PLAY')
        else:
            row.operator("tot.cleanviewanalyzer", text=tr("Clear Analyzer"), icon='X')

# 3. 贴图列表与缩放 (Image Resizer)
class TOT_PT_ImageResizer(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "3. Image Resizer"
    bl_idname = "TOT_PT_ImageResizer"
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text=tr("Image Resizer"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        # 扫描按钮
        row = layout.row()
        row.scale_y = 1.2
        row.operator("tot.updateimagelist", text=tr("Scan / Refresh Images"), icon='FILE_REFRESH')
        
        # 统计信息
        if scn.r_total_images > 0:
            box = layout.box()
            r = box.row()
            r.label(text=f"{tr('Total')}: {scn.r_total_images}")
            r.label(text=f"{tr('Mem')}: {scn.total_image_memory} MB")
        
        # 列表
        layout.template_list("TOT_UL_ImageStats", "", scn, "image_list", scn, "custom_index_image_list", rows=5)
        
        # 选择工具
        row = layout.row(align=True)
        row.operator("tot.imglistselectall", text=tr("Select All/None"), icon='CHECKBOX_HLT')
        
        layout.separator()
        layout.label(text="Resize Options:", icon='TOOL_SETTINGS')
        
        # 缩放选项
        col = layout.column(align=True)
        col.prop(scn, "resize_size", text=tr("Target"))
        if scn.resize_size == 'c':
            col.prop(scn, "custom_resize_size", text=tr("Pixels"))
            
        col.prop(scn, "duplicate_images", text=tr("Safe Mode (Copy Files)"))
        if scn.duplicate_images and not scn.use_same_directory:
             col.prop(scn, "custom_output_path", text=tr("Output"))
             
        # 执行缩放
        row = layout.row()
        row.scale_y = 1.4
        row.operator("tot.resizeimages_async", text=tr("Resize Selected Images"), icon='IMAGE_DATA')

        layout.separator()
        box_cam = layout.box()
        box_cam.label(text=tr("AI / Camera Optimization"), icon='VIEW_CAMERA')
        col = box_cam.column(align=True)
        col.label(text=tr("Auto-calculate size based on screen coverage"), icon='INFO')
        # 按钮
        col.operator("tot.optimize_by_camera", text=tr("Run Camera Optimization"), icon='SHADING_RENDERED')

        # 分辨率切换器 (Texture Switcher) ---
        layout.separator()
        box = layout.box()
        box.label(text=tr("Texture Switcher (Global)"), icon='UV_SYNC_SELECT')
        
        # 只有在保存文件后才能从文件夹加载
        row = box.row(align=True)
        row.scale_y = 1.2
        
        # 1. 原图按钮
        op = row.operator("tot.switch_resolution", text=tr("Original"), icon='FILE_IMAGE')
        op.target_res = "ORIGINAL"
        
        # 2. 动态检测已生成的文件夹，并生成对应的切换按钮
        # 这样如果没有生成 512px 的，就不显示 512 的按钮，或者你可以硬编码常用的
        base_path = bpy.path.abspath("//")
        # 2.1 检测 Camera Optimized 文件夹并显示按钮
        if base_path and os.path.exists(os.path.join(base_path, "textures_camera_optimized")):
            op = row.operator("tot.switch_resolution", text=tr("Auto-Opt"), icon='CAMERA_DATA')
            op.target_res = "camera_optimized" # 传给 Operator 的特殊字符串

        found_resolutions = []
        if base_path and os.path.exists(base_path):
            try:
                for item in os.listdir(base_path):
                    if os.path.isdir(os.path.join(base_path, item)) and item.startswith("textures_") and item.endswith("px"):
                        # 解析 "textures_1024px" -> "1024"
                        res_str = item.replace("textures_", "").replace("px", "")
                        if res_str.isdigit():
                            found_resolutions.append(res_str)
            except: pass
            
        found_resolutions.sort(key=int) # 按数字大小排序
        
        if found_resolutions:
            for res in found_resolutions:
                op = row.operator("tot.switch_resolution", text=f"{res}px")
                op.target_res = res
        else:
            row.label(text="(No resized sets found)")

# 4. LOD层级管理 (LOD Manager)
class TOT_PT_LODManager(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "4. LOD Manager"
    bl_idname = "TOT_PT_LODManager"
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text=tr("LOD Manager"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        # ==========================================================
        # Part A: 基础设置 (相机 & 距离阈值)
        # ==========================================================
        layout.prop(scn, "lod_camera", icon='CAMERA_DATA')
        
        layout.separator()
        
        # 恢复距离设置 (专门供 Viewport 使用)
        # 使用 align=True 让它们排成紧凑的一行或一列
        col = layout.column(align=True)
        col.label(text=tr("LOD Distance Levels (For Viewport):"), icon='DRIVER_DISTANCE')
        
        row = col.row(align=True)
        row.prop(scn, "lod_dist_0", text=tr("High <"))
        row.prop(scn, "lod_dist_1", text=tr("Mid <"))
        row.prop(scn, "lod_dist_2", text=tr("Low <"))
        # 超过 lod_dist_2 的即为 Far
        
        layout.separator()

        # ==========================================================
        # Part B: 视窗显示优化 (Viewport Optimization)
        # 依赖上面的距离设置
        # ==========================================================
        box = layout.box()
        header = box.row()
        header.prop(scn, "view_lod_enabled", text=tr("Viewport Optimization"), icon='VIEW3D', toggle=True)
        
        if scn.view_lod_enabled:
            col = box.column(align=True)
            
            # 使用 split 让标签和选项对齐更好看
            def draw_lod_row(layout, label, prop_name):
                row = layout.row(align=True)
                row.label(text=label)
                row.prop(scn, prop_name, text="")
            
            draw_lod_row(col, f"0m - {scn.lod_dist_0}m (High):", "view_lod0_display")
            draw_lod_row(col, f"{scn.lod_dist_0}m - {scn.lod_dist_1}m (Mid):", "view_lod1_display")
            draw_lod_row(col, f"{scn.lod_dist_1}m - {scn.lod_dist_2}m (Low):", "view_lod2_display")
            draw_lod_row(col, f"> {scn.lod_dist_2}m (Far):", "view_lod3_display")
            
            col.separator()
            col.prop(scn, "view_lod3_hide", text=tr("Hide Far Objects"))
            
            # 操作按钮
            r = box.row(align=True)
            r.scale_y = 1.2
            r.operator("tot.viewport_lod_update", text=tr("Update View"), icon='FILE_REFRESH')
            r.operator("tot.viewport_lod_reset", text=tr("Reset"), icon='X')

        # ==========================================================
        # Part C: 模型几何优化 (Geometry LOD - Screen Coverage)
        # ==========================================================
        layout.separator()
        box = layout.box()
        
        # 头部
        row = box.row()
        row.label(text=tr("Geometry LOD (Screen Ratio)"), icon="MOD_DECIM")
        row.prop(scn, "geo_lod_enabled", text=tr("Enable"), toggle=True)
        
        if scn.geo_lod_enabled:
            # 1. 方法选择
            row = box.row(align=True)
            row.prop(scn, "geo_lod_method", text=tr("Method"))
            
            # 2. 参数显示
            col = box.column(align=True)
            col.prop(scn, "geo_lod_min_faces", text=tr("Min Faces (Safety)"))
            
            # 动态显示强度标签
            if scn.geo_lod_method == 'DECIMATE':
                # 注意：i18n字典里要加上对应的key
                col.prop(scn, "geo_lod_min_ratio", text=tr("Min Ratio (Safety Floor)"), slider=True)
                col.label(text=tr("Prevents breaking close-up details"), icon='INFO')
            else:
                # 1. 强度因子 (实际上是 LOD Factor 的敏感度)
                col.prop(scn, "geo_lod_min_ratio", text=tr("GN Strength Factor"), slider=True)
                
                # 2. 最大合并距离 (这是新逻辑的核心参数，提升显示优先级)
                row = col.row(align=True)
                row.prop(scn, "geo_lod_max_dist", text=tr("Max Merge Distance"))
                row.label(text="", icon='DRIVER_DISTANCE')
                
                # 3. 提示信息更新
                # 移除了 Angle Threshold 滑块，改为提示自动保护
                box = col.box()
                box.label(text=tr("Auto Edge Protection"), icon='SHADING_WIRE')
                box.label(text=tr("Distance-based Collapse"), icon='MOD_PARTICLES')
            # 3. 三大核心按钮 (只保留这一个区域，删除原来的重复块)
            row = box.row(align=True)
            row.scale_y = 1.2
            row.operator("tot.geo_lod_setup", text=tr("Setup Modifiers"), icon="MODIFIER")
            
            # 使用 Async Update (防止卡顿)
            row.operator("tot.geo_lod_update_async", text=tr("Update Geometry (Async)"), icon="PLAY")
            
            row.operator("tot.geo_lod_reset", text=tr("Reset Geometry"), icon="FILE_REFRESH")   
            
            # 4. Apply 按钮
            row = box.row()
            row.scale_y = 1.2
            row.alert = True 
            op_text = tr("Apply Decimate (Destructive)") if scn.geo_lod_method == 'DECIMATE' else tr("Apply GeoNodes (Destructive)")
            row.operator("tot.geo_lod_apply_async", text=op_text, icon="CHECKMARK")
# 5. 去除重复贴图 (Duplicate Remover)
class TOT_PT_DuplicateRemover(TOT_PT_MainPanel, bpy.types.Panel):
    bl_label = "5. Clean Up & Storage"
    bl_idname = "TOT_PT_DuplicateRemover"
    bl_order = 5
    
    def draw_header(self, context):
        self.layout.label(text=tr("Clean Up & Storage"))

    def draw(self, context):
        layout = self.layout
        scn = context.scene.tot_props
        
        # ... (Data Cleanup 部分保持不变) ...
        box = layout.box()
        box.label(text=tr("Data Cleanup"), icon='BRUSH_DATA')
        col = box.column(align=True)
        col.operator("tot.clearduplicateimage", text=tr("Merge Duplicate Images (.001)"), icon='TRASH')

        # --- 外部文件夹管理 (修复版) ---
        box = layout.box()
        box.label(text=tr("Disk Storage Management"), icon='FILE_FOLDER')
        
        # 1. 获取绝对路径，并标准化路径分隔符
        raw_path = bpy.path.abspath("//")
        base_path = os.path.normpath(raw_path) if raw_path else None
        
        if not base_path or not os.path.exists(base_path):
            box.label(text=tr("Save file to see texture folders"), icon='ERROR')
        else:
            texture_folders = []
            try:
                # 扫描
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    # 必须是目录 且 名字匹配
                    if os.path.isdir(full_path) and item.startswith("textures_"):
                        texture_folders.append(item)
            except Exception as e:
                box.label(text=f"Scan Error: {str(e)}", icon='ERROR')
            
            if not texture_folders:
                box.label(text="No generated folders found.", icon='INFO')
            else:
                box.label(text=f"{tr('Found')} {len(texture_folders)} {tr('Texture Sets')}:", icon='FILE_IMAGE')
                
                for folder in texture_folders:
                    row = box.row()
                    row.alignment = 'EXPAND'
                    # 文件夹图标 + 名字
                    row.label(text=folder, icon='FOLDER_REDIRECT')
                    # 删除按钮
                    op = row.operator("tot.delete_texture_folder", text="", icon='X')
                    op.folder_name = folder

classes = (
    TOT_PT_Header,
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