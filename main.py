import os
import sys
import argparse
from pathlib import Path

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from epub_parser import process_epub
from text_chunker import process_chapter_text
from tts_engine import AudioGenerator
from audio_merger import generate_ffmpeg_metadata, merge_audio_with_metadata
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="Convert an EPUB file into an M4B audiobook using on-device Kokoro TTS.")
    parser.add_argument("--epub_path", type=str, default="/Users/dhruvcharan/code/AudioBookConvertor/The3rdPol.epub", help="Path to the source EPUB file.")
    parser.add_argument("--output", type=str, default="./audiobooks/", help="Directory to save the resulting .m4b file. Default is current directory.")
    parser.add_argument("--voice", type=str, default="bm_lewis", help="Voice/Speaker to use. For 'blend' use formula like 'bm_lewis*0.5+af_heart*0.5'")
    parser.add_argument("--engine", type=str, choices=["kokoro", "xtts", "blend"], default="kokoro", help="Which TTS engine to use. Default is 'kokoro'.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.epub_path):
        print(f"Error: EPUB file not found at {args.epub_path}")
        sys.exit(1)
        
    epub_name = Path(args.epub_path).stem
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary working directory for chapters
    temp_dir = out_dir / f"{epub_name}_temp"
    temp_dir.mkdir(exist_ok=True)
    
    print("====================================")
    print(f"📘 Processing EPUB: {epub_name}")
    print("====================================\n")
    
    # 1. Parse EPUB
    print("1. Extracting and sanitizing chapters from EPUB...")
    chapters = process_epub(args.epub_path)
    print(f"   Found {len(chapters)} viable chapters.\n")
    
    if not chapters:
        print("Error: Could not extract any readable text from this EPUB.")
        sys.exit(1)

    # 2. Init TTS Engine
    print(f"2. Initializing {args.engine.upper()} TTS Engine...")
    if args.engine == "kokoro":
        tts = AudioGenerator(voice=args.voice)
    elif args.engine == "blend":
        from tts_engine_blend import AudioGeneratorBlend
        tts = AudioGeneratorBlend(voice_formula=args.voice)
    else:
        from tts_engine_xtts import AudioGeneratorXTTS
        xtts_voice = args.voice if args.voice != "bm_lewis" else "Ana Florence"
        tts = AudioGeneratorXTTS(speaker=xtts_voice)
    print()
    
    chapter_audio_files = []
    
    # 3. Process Chapters
    print("3. Chunking text and generating audio...")
    
    # Pre-calculate total chunks across all chapters for highly accurate ETA
    total_chunks = sum(len(process_chapter_text(chap['text'], max_chars=400)) for chap in chapters)
    chunks_processed = 0
    
    # Running averages for time estimation
    total_audio_time = 0.0
    total_gen_time = 0.0
    
    chapter_pbar = tqdm(chapters, desc="Processing Chapters", unit="chapter")
    for i, chapter in enumerate(chapter_pbar):
        tqdm.write(f"\n   -> Working on Chapter {i+1}: {chapter['title']}")
        
        # Chunk text
        chunks = process_chapter_text(chapter['text'], max_chars=400)
        
        # Output path for this chapter
        chap_audio_path = str(temp_dir / f"chapter_{i+1:03d}.wav")
        
        # Generate Audio
        audio_duration, gen_time = tts.generate_chapter_audio(chunks, chap_audio_path)
        chapter_audio_files.append(chap_audio_path)
        
        # Update metrics
        total_audio_time += audio_duration
        total_gen_time += gen_time
        chunks_processed += len(chunks)
        
        # Calculate RTF and ETA
        if total_audio_time > 0 and total_gen_time > 0:
            current_rtf = total_gen_time / total_audio_time
            chunks_remaining = total_chunks - chunks_processed
            
            # Guess remaining time based on average generation time per chunk
            avg_time_per_chunk = total_gen_time / chunks_processed
            est_seconds_remaining = chunks_remaining * avg_time_per_chunk
            
            # Format ETA
            mins, secs = divmod(int(est_seconds_remaining), 60)
            hrs, mins = divmod(mins, 60)
            eta_str = f"{hrs:02d}h{mins:02d}m" if hrs > 0 else f"{mins:02d}m{secs:02d}s"
            
            chapter_pbar.set_postfix({
                "RTF": f"{current_rtf:.2f}x",
                "ETA": eta_str
            })
        print()
        
    # 4. Merge & Metadata
    print("4. Compiling final audiobook...")
    final_m4b_path = str(out_dir / f"{epub_name}.m4b")
    metadata_path = str(temp_dir / "metadata.txt")
    
    generate_ffmpeg_metadata(chapter_audio_files, metadata_path, book_title=epub_name)
    merge_audio_with_metadata(chapter_audio_files, metadata_path, final_m4b_path)
    
    print("\n====================================")
    print(f"✅ Conversion Complete!")
    print(f"🎉 Audiobook saved to: {final_m4b_path}")
    print("====================================")
    
    # Cleanup Temp Dir
    print("\nCleaning up temporary files...")
    for f in chapter_audio_files + [metadata_path]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
    try:
        os.rmdir(temp_dir)
    except Exception:
        pass


if __name__ == "__main__":
    main()
