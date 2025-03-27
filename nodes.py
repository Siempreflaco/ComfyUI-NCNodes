import hashlib
import io
import base64
import ffmpeg
import torchaudio
import re

class NCAudioRecorderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {    
            "required": {
                "base64_data": ("STRING", {"multiline": False}),
                "record_duration_max": ("INT",{"default": 15, "min": 1, "max": 60, "step": 1,}),
            }
        }
    
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    CATEGORY = "NCNodes/audio"
    FUNCTION = "process_audio"

    def process_audio(self, base64_data, record_duration_max):
        audio_data = base64.b64decode(base64_data)
        input_buffer = io.BytesIO(audio_data)
        output_buffer = io.BytesIO()
        process = (ffmpeg.input('pipe:0', format='webm').output('pipe:1', format='wav').run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True))
        output, _ = process.communicate(input_buffer.read())
        output_buffer.write(output)
        output_buffer.seek(0)
        waveform, sample_rate = torchaudio.load(output_buffer)

        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)

        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

        return (audio,)
    
    @classmethod
    def IS_CHANGED(s, base64_data, record_duration_max):
        m = hashlib.sha256()
        m.update(base64_data.encode())
        return m.hexdigest()

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