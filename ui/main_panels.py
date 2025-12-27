# File Path: .\ui\main_panels.py

import bpy
import os
from .. import AUTHOR_NAME
from ..i18n import ADDON_DOMAIN

def _(msg):
    return bpy.app.translations.pgettext(msg, msgctxt=ADDON_DOMAIN)

class LOD_PT_MainPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Optimize" 
    bl_options = {'DEFAULT_CLOSED'}
    bl_translation_context = ADDON_DOMAIN

class LOD_PT_Header(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "" 
    bl_idname = "LOD_PT_Header"
    bl_order = 0
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.label(text="LODify", icon='MODIFIER')
        layout.separator()

class LOD_PT_CollectionAnalyzer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "1. Collection Analyzer"
    bl_idname = "LOD_PT_CollectionAnalyzer"
    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="Collection Analyzer")

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        layout.prop(scn, "colA_Method", text="Method")
        
        if scn.colA_Method == 'm2':
            box = layout.box()
            box.label(text="Color Thresholds (Vertex %)", icon='PREFERENCES')
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
            row.operator("lod.collectionanalyzer", text="Run Analyzer", icon='PLAY')
        else:
            row.operator("lod.cleancolors", text="Clear Analyzer", icon='X')
            row.operator("lod.collectionanalyzer", text="", icon='FILE_REFRESH')

class LOD_PT_ViewAnalyzer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "2. View Analyzer"
    bl_idname = "LOD_PT_ViewAnalyzer"
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="View Analyzer")
        
    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        layout.label(text="View Analyzer", icon='SCENE_DATA')
        row = layout.row(align=True)
        row.scale_y = 1.2
        if not scn.AA_Toggle:
            row.operator("lod.viewanalyzer", text="Run Analyzer", icon='PLAY')
        else:
            row.operator("lod.cleanviewanalyzer", text="Clear Analyzer", icon='X')

class LOD_PT_ImageResizer(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "3. Image Resizer"
    bl_idname = "LOD_PT_ImageResizer"
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="Image Resizer")

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        row = layout.row()
        row.scale_y = 1.2
        row.operator("lod.updateimagelist", text="Scan / Refresh Images", icon='FILE_REFRESH')
        
        if scn.r_total_images > 0:
            box = layout.box()
            r = box.row()
            r.label(text=f"{_('Total')}: {scn.r_total_images}")
            r.label(text=f"{_('Mem')}: {scn.total_image_memory} MB")
        
        layout.template_list("LOD_UL_ImageStats", "", scn, "image_list", scn, "custom_index_image_list", rows=5)
        
        row = layout.row(align=True)
        row.operator("lod.imglistselectall", text="Select All/None", icon='CHECKBOX_HLT')
        
        layout.separator()
        layout.label(text="Resize Options:", icon='TOOL_SETTINGS')
        
        col = layout.column(align=True)
        col.prop(scn, "resize_size", text="Target")
        if scn.resize_size == 'c':
            col.prop(scn, "custom_resize_size", text="Pixels")
            
        col.prop(scn, "duplicate_images", text="Safe Mode (Copy Files)")
        if scn.duplicate_images and not scn.use_same_directory:
             col.prop(scn, "custom_output_path", text="Output")
             
        row = layout.row()
        row.scale_y = 1.4
        row.operator("lod.resizeimages_async", text="Resize Selected Images", icon='IMAGE_DATA')

        layout.separator()
        box_cam = layout.box()
        box_cam.label(text="AI / Camera Optimization", icon='VIEW_CAMERA')
        col = box_cam.column(align=True)
        col.label(text="Auto-calculate size based on screen coverage", icon='INFO')
        col.operator("lod.optimize_by_camera", text="Run Camera Optimization", icon='SHADING_RENDERED')

        layout.separator()
        box = layout.box()
        box.label(text="Texture Switcher (Global)", icon='UV_SYNC_SELECT')
        
        row = box.row(align=True)
        row.scale_y = 1.2
        
        op = row.operator("lod.switch_resolution", text="Original", icon='FILE_IMAGE')
        op.target_res = "ORIGINAL"
        
        base_path = bpy.path.abspath("//")
        if base_path and os.path.exists(os.path.join(base_path, "textures_camera_optimized")):
            op = row.operator("lod.switch_resolution", text="Auto-Opt", icon='CAMERA_DATA')
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
            row.label(text="(No resized sets found)")

class LOD_PT_LODManager(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "4. LOD Manager"
    bl_idname = "LOD_PT_LODManager"
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="LOD Manager")

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        layout.prop(scn, "lod_camera", text="LOD Camera", icon='CAMERA_DATA')
        layout.separator()
        
        col = layout.column(align=True)
        col.label(text="LOD Distance Levels (For Viewport)", icon='DRIVER_DISTANCE')
        
        row = col.row(align=True)
        row.prop(scn, "lod_dist_0", text="High <")
        row.prop(scn, "lod_dist_1", text="Mid <")
        row.prop(scn, "lod_dist_2", text="Low <")
        
        layout.separator()

        box = layout.box()
        header = box.row()
        header.prop(scn, "view_lod_enabled", text="Viewport Optimization", icon='VIEW3D', toggle=True)
        
        if scn.view_lod_enabled:
            col = box.column(align=True)
            def draw_lod_row(layout, label, prop_name):
                row = layout.row(align=True)
                row.label(text=label)
                row.prop(scn, prop_name, text="")
            
            draw_lod_row(col, f"0m - {scn.lod_dist_0}m ({_('High <')}):", "view_lod0_display")
            draw_lod_row(col, f"{scn.lod_dist_0}m - {scn.lod_dist_1}m ({_('Mid <')}):", "view_lod1_display")
            draw_lod_row(col, f"{scn.lod_dist_1}m - {scn.lod_dist_2}m ({_('Low <')}):", "view_lod2_display")
            draw_lod_row(col, f"> {scn.lod_dist_2}m (Far):", "view_lod3_display")
            
            col.separator()
            col.prop(scn, "view_lod3_hide", text="Hide Far Objects")
            
            r = box.row(align=True)
            r.scale_y = 1.2
            r.operator("lod.viewport_lod_update", text="Update View", icon='FILE_REFRESH')
            r.operator("lod.viewport_lod_reset", text="Reset", icon='X')

        layout.separator()
        box = layout.box()
        
        row = box.row()
        row.label(text="Geometry LOD (Screen Ratio)", icon="MOD_DECIM")
        row.prop(scn, "geo_lod_enabled", text="Enable", toggle=True)
        
        if scn.geo_lod_enabled:
            row = box.row(align=True)
            row.prop(scn, "geo_lod_method", text="Method")
            
            col = box.column(align=True)
            col.prop(scn, "geo_lod_min_faces", text="Min Faces (Safety)")
            
            if scn.geo_lod_method == 'DECIMATE':
                col.prop(scn, "geo_lod_min_ratio", text="Min Ratio (Safety Floor)", slider=True)
                col.label(text="Prevents breaking close-up details", icon='INFO')
            else:
                col.prop(scn, "geo_lod_min_ratio", text="GN Strength Factor", slider=True)
                row = col.row(align=True)
                row.prop(scn, "geo_lod_max_dist", text="Max Merge Distance")
                row.label(text="", icon='DRIVER_DISTANCE')
                
                box_in = col.box()
                box_in.label(text="Auto Edge Protection", icon='SHADING_WIRE')
                box_in.label(text="Distance-based Collapse", icon='MOD_PARTICLES')
            
            row = box.row(align=True)
            row.scale_y = 1.2
            row.operator("lod.geo_lod_setup", text="Setup Modifiers", icon="MODIFIER")
            row.operator("lod.geo_lod_update_async", text="Update Geometry (Async)", icon="PLAY")
            row.operator("lod.geo_lod_reset", text="Reset Geometry", icon="FILE_REFRESH")   
            
            row = box.row()
            row.scale_y = 1.2
            row.alert = True 
            op_text = ("Apply Decimate (Destructive)") if scn.geo_lod_method == 'DECIMATE' else ("Apply GeoNodes (Destructive)")
            row.operator("lod.geo_lod_apply_async", text=op_text, icon="CHECKMARK")

class LOD_PT_DuplicateRemover(LOD_PT_MainPanel, bpy.types.Panel):
    bl_label = "5. Clean Up & Storage"
    bl_idname = "LOD_PT_DuplicateRemover"
    bl_order = 5
    
    def draw_header(self, context):
        self.layout.label(text="Clean Up & Storage")

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        box = layout.box()
        box.label(text="Data Cleanup", icon='BRUSH_DATA')
        col = box.column(align=True)
        col.operator("lod.clearduplicateimage", text="Merge Duplicate Images (.001)", icon='TRASH')

        box = layout.box()
        box.label(text="Disk Storage Management", icon='FILE_FOLDER')
        
        raw_path = bpy.path.abspath("//")
        base_path = os.path.normpath(raw_path) if raw_path else None
        
        if not base_path or not os.path.exists(base_path):
            box.label(text="Save file to see texture folders", icon='ERROR')
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
                box.label(text="No generated folders found.", icon='INFO')
            else:
                box.label(text=f"{_('Found')} {len(texture_folders)} {_('Texture Sets')}:", icon='FILE_IMAGE')
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
        self.layout.label(text="Experimental Features")

    def draw(self, context):
        layout = self.layout
        scn = context.scene.lod_props
        
        box_lod = layout.box()
        row = box_lod.row()
        row.label(text="Shader Detail LOD", icon='SHADING_RENDERED')
        row.prop(scn, "exp_shader_lod_enabled", text="Enable", toggle=True)
        
        if scn.exp_shader_lod_enabled:
            col = box_lod.column(align=True)
            col.label(text="Normal Map Strength Multipliers", icon='NODE_MATERIAL')
            def draw_mult_row(layout, label, prop_name):
                row = layout.row(align=True)
                row.label(text=label); row.prop(scn, prop_name, text="")
            draw_mult_row(col, f"LOD 1 ({_('Mid <')}):", "exp_normal_mult_1")
            draw_mult_row(col, f"LOD 2 ({_('Low <')}):", "exp_normal_mult_2")
            draw_mult_row(col, f"LOD 3 (Far):", "exp_normal_mult_3")
            col.separator()
            col.label(text="Displacement Scale Multipliers", icon='MOD_DISPLACE')
            draw_mult_row(col, f"LOD 1 ({_('Mid <')}):", "exp_disp_mult_1")
            draw_mult_row(col, f"LOD 2 ({_('Low <')}):", "exp_disp_mult_2")
            draw_mult_row(col, f"LOD 3 (Far):", "exp_disp_mult_3")
            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("lod.shader_lod_update_async", text="Update Shaders", icon='PLAY')
            row.operator("lod.shader_lod_reset", text="Reset", icon='LOOP_BACK')
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