import os
import time
import torch
import numpy as np
import soundfile as sf
import re
from typing import List, Tuple, Dict
from kokoro import KPipeline
from tts_engine import get_optimal_device

class AudioGeneratorBlend:
    """
    An advanced extension of the Kokoro TTS engine that supports mathematical
    voice blending formulas on raw PyTorch tensors.
    
    Example Voice Strings:
    - "bm_lewis" (Standard single voice)
    - "bm_lewis*0.5+bm_george*0.5" (Blended voice)
    - "af_heart*0.8+hf_alpha*0.2"
    """
    def __init__(self, voice_formula: str = 'af_heart*0.5+bm_lewis*0.5'):
        self.device = get_optimal_device()
        self.lang_code = 'a' # American English
        self.voice_formula = voice_formula
        self.custom_voice_id = "custom_blend"
        
        print(f"Loading Blending Pipeline with formula '{self.voice_formula}' on {self.device}...")
        self.pipeline = KPipeline(lang_code=self.lang_code, device=self.device, repo_id='hexgrad/Kokoro-82M')
        
        # Parse the formula and build the custom tensor
        self.blended_tensor = self._build_blended_tensor(self.voice_formula)
        
        # Monkey-patch the pipeline's load_voice to intercept our custom name
        self._original_load_voice = self.pipeline.load_voice
        self.pipeline.load_voice = self._intercept_load_voice
        print("Blended Pipeline successfully initialized.")

    def _build_blended_tensor(self, formula: str) -> torch.Tensor:
        """
        Parses mathematical formulas like 'bm_lewis*0.5+bm_george*0.5',
        loads the raw tensor weights from HuggingFace, scales them,
        and adds them together.
        """
        try:
            parts = formula.split('+')
            combined = None
            
            for part in parts:
                part = part.strip()
                if '*' in part:
                    voice_name, weight_str = part.split('*')
                    weight = float(weight_str)
                else:
                    voice_name = part
                    weight = 1.0
                    
                voice_name = voice_name.strip()
                print(f"   -> Loading base tensor '{voice_name}' with weight {weight}")
                
                # Load the raw PyTorch tensor for this specific voice
                pack = self.pipeline.load_voice(voice_name).to(self.device)
                
                if combined is None:
                    combined = pack * weight
                else:
                    combined += pack * weight
                    
            return combined
        except Exception as e:
            print(f"Error parsing voice blending formula '{formula}': {e}")
            print("Falling back to standard 'af_heart' voice.")
            return self.pipeline.load_voice('af_heart').to(self.device)

    def _intercept_load_voice(self, voice: str):
        """
        Overrides the pipeline's native loading logic to inject our custom tensor caching.
        """
        if voice == self.custom_voice_id:
            return self.blended_tensor
        return self._original_load_voice(voice)

    def generate_chapter_audio(self, chunks: List[str], output_path: str) -> Tuple[float, float]:
        """
        Batches audio chunks and compiles with the custom blended tensor.
        Returns: (audio_duration_seconds, generation_time_seconds)
        """
        if not chunks:
            return 0.0, 0.0

        all_audio = []
        sample_rate = 24000
        silence_array = np.zeros(int(sample_rate * 1.0), dtype=np.float32)
        start_time = time.time()
        
        from tqdm import tqdm
        
        # Pass list to KPipeline natively, but force our custom voice id to trigger the intercept
        generator = self.pipeline(chunks, voice=self.custom_voice_id, speed=1.0, split_pattern=r'\n+')
        
        for i, (_, _, audio_array) in enumerate(tqdm(generator, total=len(chunks), desc="  Generating Blended Audio", leave=False)):
            if audio_array is not None and len(audio_array) > 0:
                all_audio.append(audio_array)
                
            if i < len(chunks) - 1:
                original_text = chunks[i]
                if original_text.endswith('\n\n') or original_text.endswith('\n'):
                    all_audio.append(silence_array)
        
        generation_time = time.time() - start_time
        
        if not all_audio:
            print("Warning: TTS failed to generate any blended audio arrays.")
            return 0.0, 0.0
            
        final_audio = np.concatenate(all_audio)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        sf.write(output_path, final_audio, sample_rate)
        return float(len(final_audio) / sample_rate), generation_time

if __name__ == "__main__":
    print("Testing AudioGeneratorBlend...")
    tts = AudioGeneratorBlend(voice_formula="af_heart*0.7+bm_lewis*0.3")
    tts.generate_chapter_audio(["This is a test of the advanced mathematical voice blending system.\n\n"], "test_blend.wav")
    print("Test complete. Check test_blend.wav")
