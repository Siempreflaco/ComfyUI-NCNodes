import re

class NCLineCounter:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string_text": ("STRING", {"multiline": True,"default":"text"}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("Lines", "Lines-1")

    FUNCTION = "count_lines"
    CATEGORY = "NCNodes/Utils"
    
    def count_lines(self, string_text):
        #count lines
        string_text = string_text.strip() #strip extra line feeds
        string_text = string_text.strip()
        string_text = re.sub(r'((\n){2,})', '\n', string_text)
        lines = string_text.split('\n')
        num_lines = len(lines)
        return (num_lines,num_lines-1,)
			
class NCIncrementINT:
    def __init__(self):
        self.counters = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["increment", "increment_to_stop", "increment_to_stop_loop"],),
                "stop": ("INT", {"default": 5, "min": 0, "max": 99999, "step": 1}),
                "step": ("INT", {"default": 1, "min": 0, "max": 99999, "step": 1}),
            },
            "optional": {
                "reset_counter": ("BOOLEAN", {"default": False}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("INT",)
    FUNCTION = "increment_number"

    CATEGORY = "NCNodes/Utils"

    def increment_number(self, mode, stop, step, unique_id, reset_counter):

        counter = -1
        if self.counters.__contains__(unique_id):
            counter = self.counters[unique_id]

        if reset_counter == True:
            counter = -1

        if mode == 'increment':
            counter += step
        elif mode == 'increment_to_stop':
            counter = counter + step if counter < stop else counter
        elif mode == 'increment_to_stop_loop':
            counter = counter + step if counter < stop else 0

        self.counters[unique_id] = counter

        return (counter,)