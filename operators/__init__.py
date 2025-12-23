from . import analyzer
from . import image
from . import viewport  
from . import geometry 
from . import shader_lod
import bpy

def register():
    bpy.utils.register_class(LOD_OT_RunAllOptimization)

def unregister():
    bpy.utils.unregister_class(LOD_OT_RunAllOptimization)