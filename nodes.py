import hashlib
import io
import base64
import ffmpeg
import torchaudio

class NCAudioRecorderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {    
            "required": {
                "base64_data": ("STRING", {"multiline": False}),
                "record_mode": (["press_and_hold", "start_and_stop"],{"default":"start_and_stop",}),
                "record_duration_max": ("INT",{"default": 15, "min": 1, "max": 60, "step": 1,}),
                "new_generation_after_recording": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    CATEGORY = "NCNodes/audio"
    FUNCTION = "process_audio"

    def process_audio(self, base64_data, record_mode, record_duration_max, new_generation_after_recording):
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
    def IS_CHANGED(s, base64_data, record_mode, record_duration_max, new_generation_after_recording):
        m = hashlib.sha256()
        m.update(base64_data.encode())
        return m.hexdigest()
