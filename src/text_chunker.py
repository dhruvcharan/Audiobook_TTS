import re
from typing import List
import nltk

def normalize_text(text: str) -> str:
    """
    Expands common symbols and performs basic normalization
    to prevent the TTS engine from reading formatting artifacts
    or mispronouncing symbols.
    """
    # Replace common symbols with words
    replacements = {
        '&': 'and',
        '%': 'percent',
        '@': 'at',
        '#': 'hashtag',
        '$': 'dollars',
        '£': 'pounds',
        '€': 'euros',
        '~': '',  # usually a formatting artifact
        '_': ' ', # remove underscores
        '*': '',  # remove markdown asterisks
    }
    
    for symbol, word in replacements.items():
        text = text.replace(symbol, word)
        
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()

def chunk_text(text: str, max_chars: int = 400) -> List[str]:
    """
    Splits a large string of text into smaller chunks suitable for TTS inference.
    Uses NLTK sentence tokenization so it doesn't split sentences midway.
    
    Args:
        text (str): The large text to chunk
        max_chars (int): The maximum character length of a single chunk.
                         TTS models usually perform best under 500 characters.
                         
    Returns:
        List[str]: A list of text chunks
    """
    if not text:
        return []

    # First, tokenize the text into independent sentences
    try:
        sentences = nltk.tokenize.sent_tokenize(text)
    except LookupError:
        # Fallback if NLTK data isn't downloaded for some reason
        print("Warning: NLTK 'punkt' not found. Splitting by periods.")
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If a single sentence is incredibly long (rare, but happens),
        # we are forced to chunk it by commas or roughly by character limit.
        if len(sentence) > max_chars:
            # Add the current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Split the mega-sentence by roughly equal parts or commas (simplified here)
            # A more robust solution would slice at nearest word boundary
            words = sentence.split(" ")
            mega_chunk = ""
            for word in words:
                if len(mega_chunk) + len(word) + 1 > max_chars:
                    chunks.append(mega_chunk.strip())
                    mega_chunk = ""
                mega_chunk += word + " "
            
            if mega_chunk:
                chunks.append(mega_chunk.strip())
            continue

        # Normal operation: add sentence to current chunk if it fits
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + " "
        else:
            # Chunk is full, save it and start a new one
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    # Add the final leftover chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def process_chapter_text(chapter_text: str, max_chars: int = 400) -> List[str]:
    """
    Orchestration function: normalizes the text and chunks it.
    """
    normalized = normalize_text(chapter_text)
    return chunk_text(normalized, max_chars)

if __name__ == "__main__":
    # Simple self-test code block
    sample = "Hello there! This is a test. It costs $50. How are you doing today? " * 10
    chunks = process_chapter_text(sample, max_chars=100)
    print(f"Generated {len(chunks)} chunks.")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {c}")
