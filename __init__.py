from .nodes import *
from .audio_nodes import *
from .image_process_node import *

__version__ = "1.0.0"

NODE_CLASS_MAPPINGS = {
    "NCAudioRecorderNode": NCAudioRecorderNode,
	"NCLineCounter": NCLineCounter,
	"NCIncrementINT": NCIncrementINT,
    "NCImageProcessor": NCImageProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NCAudioRecorderNode": "NC Audio Recorder",
	"NCLineCounter": "NC Line Counter",
	"NCIncrementINT": "NC Increment INT",
    "NCImageProcessor": "NC Image Processor"
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

