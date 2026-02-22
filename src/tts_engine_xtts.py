import os
import torch
import soundfile as sf
import numpy as np
import warnings
from typing import List
from tqdm import tqdm

from TTS.api import TTS

# Suppress PyTorch/TTS warnings during inference
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from TTS.api import TTS

# PyTorch 2.6+ defaults torch.load to weights_only=True, which breaks Coqui TTS checkpoints.
# We temporarily mock torch.load to default to False.
_original_load = torch.load
def _unsafe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)

torch.load = _unsafe_load

def get_optimal_device() -> str:
    """
    Detects the best available PyTorch device. 
    XTTSv2 heavily benefits from MPS (Apple Silicon) or CUDA.
    """
    if torch.backends.mps.is_available():
        print("Hardware Acceleration: Using Apple Silicon MPS")
        return "mps"
    elif torch.cuda.is_available():
        print("Hardware Acceleration: Using NVIDIA CUDA")
        return "cuda"
    else:
        print("Hardware Acceleration: Using CPU (This will be very slow for XTTS)")
        return "cpu"

class AudioGeneratorXTTS:
    def __init__(self, speaker: str = 'Ana Florence'):
        """
        Initializes the XTTSv2 pipeline via Coqui TTS.
        Requires agreeing to the Coqui Public Model License.
        Downloads ~2.5GB of weights on first run.
        """
        self.device = get_optimal_device()
        self.language = "en"
        
        # Built-in XTTS speakers. You can see the full list by initializing the model
        # and checking `tts.speakers`. E.g., 'Ana Florence', 'Claribel Dervla', 'Daisy Studious'
        self.speaker = speaker
        
        print(f"Loading XTTSv2 Pipeline with speaker '{self.speaker}' on {self.device}...")
        print("Note: First run will download ~2.5GB of model weights.")
        
        # Load the XTTSv2 model. We tell it to load directly to MPS/CUDA.
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

    def generate_chapter_audio(self, chunks: List[str], output_path: str) -> None:
        """
        Iterates over text chunks, generates numpy audio arrays via XTTS,
        concatenates them, and saves to a WAV file.
        """
        if not chunks:
            print("No text chunks provided for audio generation.")
            return

        print(f"Generating audio for {len(chunks)} chunks -> {output_path}")
        
        all_audio = []
        # XTTSv2 generates audio at 24kHz natively.
        sample_rate = 24000 
        
        for text_chunk in tqdm(chunks, desc="  Generating Chunks (XTTSv2)", leave=False):
            # The TTS.tts() method returns a list of floats (the audio waveform).
            # We must pass the text, the target speaker, and the language.
            try:
                wav_list = self.tts.tts(text=text_chunk, speaker=self.speaker, language=self.language)
                
                # Convert list to numpy array
                if wav_list:
                    audio_array = np.array(wav_list, dtype=np.float32)
                    all_audio.append(audio_array)
            except Exception as e:
                print(f"\nWarning: XTTS failed on chunk: '{text_chunk[:50]}...' Error: {e}")
        
        if not all_audio:
            print("Warning: XTTS failed to generate any audio arrays.")
            return
            
        # Concatenate all numpy audio chunks into one large array
        final_audio = np.concatenate(all_audio)
        
        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        # Write to disk using SoundFile
        print(f"Encoding {len(final_audio)} frames to {output_path}")
        sf.write(output_path, final_audio, sample_rate)

if __name__ == "__main__":
    # Standalone Test
    print("--- Testing XTTSv2 ---")
    
    # We will use text_chunker to properly format our test paragraph
    import sys
    sys.path.append(os.path.dirname(__file__))
    try:
        from text_chunker import process_chapter_text
    except ImportError:
        print("Error: Could not import text_chunker. Make sure this runs from within the project structure.")
        sys.exit(1)
        
    sample_paragraph = """
    "I can't believe it," she whispered, her voice trembling slightly in the cold night air. 
    He looked away, staring into the dark forest. "Believe it," he replied flatly. "They knew we were coming."
    This model, XTTS version 2, is highly expressive. It understands dialogue, punctuation, and pacing much better than smaller models. 
    It can be a fantastic choice for dramatic audiobooks.
    """
    
    chunks = process_chapter_text(sample_paragraph, max_chars=250)
    
    # Initialize Generator (Defaulting to 'Ana Florence' - a good standard female narrator voice)
    generator = AudioGeneratorXTTS(speaker='Ana Florence')
    
    output_file = "./test_xtts_output.wav"
    generator.generate_chapter_audio(chunks, output_file)
    print(f"\n✅ Success! XTTS test audio saved to {output_file}")
    print("Please play this file to hear the emotive nuance.")
