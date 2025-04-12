from .utility_nodes import *
from .audio_nodes import *
from .image_nodes import *
from .mesh_nodes import *

__version__ = "1.0.0"

NODE_CLASS_MAPPINGS = {
    "NCAudioRecorderNode": NCAudioRecorderNode,
	"NCLineCounter": NCLineCounter,
	"NCIncrementINT": NCIncrementINT,
    "NCImageProcessor": NCImageProcessor,
    "Load3DMesh": Load3DMesh,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NCAudioRecorderNode": "NC Audio Recorder",
	"NCLineCounter": "NC Line Counter",
	"NCIncrementINT": "NC Increment INT",
    "NCImageProcessor": "NC Image Processor",
    "Load3DMesh": "NC Load 3D Mesh From Outputs"
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

