import os
import sys
import time
import wave
import contextlib

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from text_chunker import process_chapter_text
from tts_engine import AudioGenerator
from tts_engine_xtts import AudioGeneratorXTTS

def get_audio_duration(file_path: str) -> float:
    """Returns the duration of a wav file in seconds."""
    with contextlib.closing(wave.open(file_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return duration

def run_benchmark():
    print("====================================")
    print("🏆 TTS Engine Performance Benchmark")
    print("====================================\n")
    
    # A large selection of diverse structural excerpts to test total generation time and bounds chunking
    excerpts = [
        # 1. Philosophical / Dramatic (The Master and Margarita by Mikhail Bulgakov)
        '''"But would you kindly ponder this question: What would your good do if evil didn't exist, and what would the earth look like if all the shadows disappeared? After all, shadows are cast by things and people. Here is the shadow of my sword. But shadows also come from trees and living beings. Do you want to strip the earth of all trees and living things just because of your fantasy of enjoying naked light? You're stupid."
        "I won't argue with you, old sophist," answered Matthew Levi.
        "You can't argue with me, for the reason I just mentioned: you're stupid," Woland answered and asked, "Now tell me, briefly, without tiring me, why did you appear?"''',

        # 2. Analytical / Fast-paced Mystery (The Adventures of Sherlock Holmes by Arthur Conan Doyle)
        '''"You see, but you do not observe. The distinction is clear. For example, you have frequently seen the steps which lead up from the hall to this room."
        "Frequently."
        "How often?"
        "Well, some hundreds of times."
        "Then how many are there?"
        "How many? I don't know."
        "Quite so! You have not observed. And yet you have seen. That is just my point. Now, I know that there are seventeen steps, because I have both seen and observed."''',

        # 3. Descriptive / Melancholic (The Great Gatsby by F. Scott Fitzgerald)
        '''And as I sat there brooding on the old, unknown world, I thought of Gatsby's wonder when he first picked out the green light at the end of Daisy's dock. He had come a long way to this blue lawn, and his dream must have seemed so close that he could hardly fail to grasp it. He did not know that it was already behind him, somewhere back in that vast obscurity beyond the city, where the dark fields of the republic rolled on under the night.''',

        # 4. Tense / Sci-Fi (Dune by Frank Herbert)
        '''"I must not fear. Fear is the mind-killer. Fear is the little-death that brings total obliteration. I will face my fear. I will permit it to pass over me and through me. And when it has gone past I will turn the inner eye to see its path. Where the fear has gone there will be nothing. Only I will remain."''',

        # 5. Grand / High Fantasy (The Lord of the Rings by J.R.R. Tolkien)
        '''"I wish it need not have happened in my time," said Frodo.
        "So do I," said Gandalf, "and so do all who live to see such times. But that is not for them to decide. All we have to decide is what to do with the time that is given us."''',

        # 6. Gothic / Bizarre (Titus Groan / Gormenghast by Mervyn Peake)
        '''Gormenghast, that is, the main massing of the original stone, taken by itself would have displayed a certain ponderous architectural quality were it possible to have ignored the circumvallation of those mean dwellings that swarmed like an epidemic around its outer walls. They sprawled over the sloping earth, each one half way over its neighbour until, held back by the castle ramparts, the innermost of these hovels laid hold on the great walls, clamping themselves thereto like limpets to a rock. These dwellings, by ancient law, were granted this intimacy with the stronghold, usually reserved for the aristocracy.''',

        # 7. Cyberpunk / Gritty (Neuromancer by William Gibson)
        '''The sky above the port was the color of television, tuned to a dead channel.
        "It's not like I'm using," Case heard someone say, as he shouldered his way through the crowd around the door of the Chat. "It's like my body's developed this massive drug deficiency." It was a Sprawl voice and a Sprawl joke.''',

        # 8. Classic Dystopian (1984 by George Orwell)
        '''It was a bright cold day in April, and the clocks were striking thirteen. Winston Smith, his chin nuzzled into his breast in an effort to escape the vile wind, slipped quickly through the glass doors of Victory Mansions, though not quickly enough to prevent a swirl of gritty dust from entering along with him.''',

        # 9. Whimsical / Fantasy (Alice's Adventures in Wonderland by Lewis Carroll)
        '''"But I don’t want to go among mad people," Alice remarked.
        "Oh, you can’t help that," said the Cat: "we’re all mad here. I’m mad. You’re mad."
        "How do you know I’m mad?" said Alice.
        "You must be," said the Cat, "or you wouldn’t have come here."''',

        # 10. Bleak / Post-Apocalyptic (The Road by Cormac McCarthy)
        '''He walked out in the gray light and stood and he saw for a brief moment the absolute truth of the world. The cold relentless circling of the intestate earth. Darkness implacable. The blind dogs of the sun in their running. The crushing black vacuum of the universe. And somewhere two hunted animals trembling like ground-foxes in their cover. Borrowed time and borrowed world and borrowed eyes with which to sorrow it.''',

        # 11. Horror / Classical (Frankenstein by Mary Shelley)
        '''I saw the dull yellow eye of the creature open; it breathed hard, and a convulsive motion agitated its limbs.
        How can I describe my emotions at this catastrophe, or how delineate the wretch whom with such infinite pains and care I had endeavoured to form? His limbs were in proportion, and I had selected his features as beautiful. Beautiful! Great God! His yellow skin scarcely covered the work of muscles and arteries beneath...''',

        # 12. Satirical / Sci-Fi (The Hitchhiker's Guide to the Galaxy by Douglas Adams)
        '''The ships hung in the sky in much the same way that bricks don't.
        And as the first one came to a halt, hovering silently over the city, the people below stopped and stared. Not a soul moved. Not a single car engine was left running. The entire population was gripped by an unearthly silence, waiting for whatever it was that these monolithic structures intended to do.''',
        
        # 13. Historical / Tragic (A Tale of Two Cities by Charles Dickens)
        '''It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of light, it was the season of darkness, it was the spring of hope, it was the winter of despair.''',
        
        # 14. Realism / Introspective (Crime and Punishment by Fyodor Dostoevsky)
        '''He was so immersed in himself and had isolated himself so much from everyone that he was afraid not only of meeting his landlady but of meeting anyone at all. He was crushed by poverty; but even his strained circumstances had lately ceased to burden him. He had completely given up attending to his daily affairs and did not want to attend to them. As a matter of fact, he was not afraid of any landlady, whatever she might be plotting against him.''',

        # 15. Epic / Foundational (The Iliad by Homer - Samuel Butler translation)
        '''Sing, O goddess, the anger of Achilles son of Peleus, that brought countless ills upon the Achaeans. Many a brave soul did it send hurrying down to Hades, and many a hero did it yield a prey to dogs and vultures, for so were the counsels of Jove fulfilled from the day on which the son of Atreus, king of men, and great Achilles, first fell out with one another.'''
    ]
    
    # Join all 15 excerpts sequentially to create a massive continuous text block
    large_text = "\n\n***\n\n".join(excerpts)

    
    # Proper sentence-aware chunking for TTS bounds limit
    test_chunks = process_chapter_text(large_text, max_chars=400)
    
    print(f"Sample length: {len(large_text)} characters")
    print(f"Divided into {len(test_chunks)} chunks for generation.\n")
    
    output_dir = "benchmark_results"
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}

    # --- Benchmark 1: Kokoro v1.0 ---
    print("--- 1. Testing Kokoro v1.0 (Stable, Fast) ---")
    start_init = time.time()
    kokoro_generator = AudioGenerator(voice="bm_lewis")
    kokoro_init_time = time.time() - start_init
    print(f"Init Time: {kokoro_init_time:.2f}s")
    
    kokoro_out = os.path.join(output_dir, "kokoro_test.wav")
    
    start_gen = time.time()
    kokoro_generator.generate_chapter_audio(test_chunks, kokoro_out)
    kokoro_gen_time = time.time() - start_gen
    
    kokoro_audio_len = get_audio_duration(kokoro_out)
    kokoro_rtf = kokoro_gen_time / kokoro_audio_len
    
    print(f"Generation Time: {kokoro_gen_time:.2f}s")
    print(f"Audio Produced: {kokoro_audio_len:.2f}s")
    print(f"Real-Time Factor (RTF): {kokoro_rtf:.3f}x (Lower is better)\n")
    
    results['Kokoro'] = {
        'init': kokoro_init_time,
        'gen': kokoro_gen_time,
        'audio': kokoro_audio_len,
        'rtf': kokoro_rtf
    }
    
    # Release memory before loading next massive model
    del kokoro_generator

    # --- Benchmark 2: XTTS v2 ---
    print("--- 2. Testing XTTSv2 (Expressive, Heavy) ---")
    start_init = time.time()
    xtts_generator = AudioGeneratorXTTS(speaker="Ana Florence")
    xtts_init_time = time.time() - start_init
    print(f"Init Time: {xtts_init_time:.2f}s")
    
    xtts_out = os.path.join(output_dir, "xtts_test.wav")
    
    start_gen = time.time()
    xtts_generator.generate_chapter_audio(test_chunks, xtts_out)
    xtts_gen_time = time.time() - start_gen
    
    xtts_audio_len = get_audio_duration(xtts_out)
    xtts_rtf = xtts_gen_time / xtts_audio_len
    
    print(f"Generation Time: {xtts_gen_time:.2f}s")
    print(f"Audio Produced: {xtts_audio_len:.2f}s")
    print(f"Real-Time Factor (RTF): {xtts_rtf:.3f}x (Lower is better)\n")
    
    results['XTTSv2'] = {
        'init': xtts_init_time,
        'gen': xtts_gen_time,
        'audio': xtts_audio_len,
        'rtf': xtts_rtf
    }
    
    # --- Final Comparison ---
    print("====================================")
    print("📊 Benchmark Results Summary")
    print("====================================")
    print(f"{'Metric':<20} | {'Kokoro (82M)':<15} | {'XTTSv2 (850M)':<15}")
    print("-" * 56)
    print(f"{'Init Time':<20} | {results['Kokoro']['init']:.2f}s{'':<9} | {results['XTTSv2']['init']:.2f}s")
    print(f"{'Generation Time':<20} | {results['Kokoro']['gen']:.2f}s{'':<9} | {results['XTTSv2']['gen']:.2f}s")
    print(f"{'Audio Duration':<20} | {results['Kokoro']['audio']:.2f}s{'':<9} | {results['XTTSv2']['audio']:.2f}s")
    print(f"{'Real-Time Factor':<20} | {results['Kokoro']['rtf']:.3f}x{'':<8} | {results['XTTSv2']['rtf']:.3f}x")
    print("====================================")
    
    speedup = results['XTTSv2']['rtf'] / results['Kokoro']['rtf']
    print(f"\nConclusion: Kokoro is {speedup:.1f}x faster than XTTSv2.")

if __name__ == "__main__":
    run_benchmark()
