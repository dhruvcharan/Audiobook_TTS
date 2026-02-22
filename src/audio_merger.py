import os
import subprocess
import soundfile as sf
from typing import List

def parse_time(seconds: float) -> str:
    """Converts duration in seconds to FFMPEG MS timebase format (nanoseconds) or similar acceptable formats.
    FFMPEG metadata format usually expects time in milliseconds for START/END.
    """
    return str(int(seconds * 1000))

def generate_ffmpeg_metadata(chapter_files: List[str], metadata_path: str, book_title: str) -> None:
    """
    Reads the duration of each chapter audio file, and generates an FFMPEG metadata format file.
    """
    print(f"Generating FFMPEG metadata -> {metadata_path}")
    
    with open(metadata_path, 'w') as f:
        f.write(";FFMETADATA1\n")
        f.write(f"title={book_title}\n\n")
        
        current_time_ms = 0
        
        for i, filepath in enumerate(chapter_files):
            file_info = sf.info(filepath)
            duration_ms = int(file_info.frames / file_info.samplerate * 1000)
            
            end_time_ms = current_time_ms + duration_ms
            
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={current_time_ms}\n")
            f.write(f"END={end_time_ms}\n")
            f.write(f"title=Chapter {i+1}\n\n")
            
            current_time_ms = end_time_ms

def merge_audio_with_metadata(chapter_files: List[str], metadata_path: str, output_m4b: str) -> None:
    """
    Uses FFMPEG via subprocess to concatenate the audio files, inject the chapter metadata, 
    and output a final .m4b file.
    """
    # Create a temporary concat file
    concat_file_path = os.path.join(os.path.dirname(metadata_path), "concat_list.txt")
    with open(concat_file_path, 'w') as f:
        for filepath in chapter_files:
            # ffmpeg concat demuxer expects paths in a specific format
            abs_path = os.path.abspath(filepath)
            f.write(f"file '{abs_path}'\n")

    print(f"Merging {len(chapter_files)} audio files into {output_m4b}...")
    
    command = [
        "ffmpeg",
        "-y", # Overwrite output if exists
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file_path,
        "-i", metadata_path,
        "-map_metadata", "1", # Map metadata from second input (metadata.txt)
        "-c:a", "aac",        # Encode to AAC for M4B
        "-b:a", "64k",        # 64kbps is generally plenty for spoken voice
        "-vn",                # No video
        output_m4b
    ]
    
    try:
        # Run FFMPEG
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"Successfully compiled audiobook: {output_m4b}")
    except subprocess.CalledProcessError as e:
        print(f"FFMPEG Error:\n{e.stderr.decode('utf-8')}")
        raise
    finally:
        # Cleanup concat list
        if os.path.exists(concat_file_path):
            os.remove(concat_file_path)

if __name__ == "__main__":
    # Test stub
    print("Audio Merger loaded.")
