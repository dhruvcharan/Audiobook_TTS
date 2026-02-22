import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings

# Suppress some common ebooklib warnings about missing navigation XMLs
warnings.filterwarnings("ignore", category=UserWarning, module='ebooklib')

def extract_chapters_from_epub(epub_path: str) -> list[dict]:
    """
    Reads an EPUB file and extracts its chapters (HTML items from the spine).
    Returns a list of dictionaries, each containing 'title' and 'raw_html'.
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
        
    book = epub.read_epub(epub_path)
    chapters = []
    
    # Iterate through the document spine
    for item_id_tuple in book.spine:
        # The spine item is a tuple: (item_id, linear_flag)
        item_id = item_id_tuple[0]
        item = book.get_item_with_id(item_id)
        
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append({
                'title': item.get_name(), # Usually a filename like 'chapter_1.xhtml'
                'raw_html': item.get_content()
            })
            
    return chapters

def sanitize_html_to_text(html_content: bytes | str) -> str:
    """
    Uses BeautifulSoup to strip XML/HTML tags, remove scripts/styles,
    and return clean narrative plain text.
    """
    if not html_content:
        return ""
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove elements we definitely don't want spoken
    decompose_targets = [
        # Structural / Metadata
        "script", "style", "meta", "link", "img", "image", "svg",
        
        # Tables and their internal structural elements
        "table", "tr", "td", "th", "col", "colgroup", "thead", "tbody", "tfoot",
        
        # Technical Code Blocks
        "pre", "code", "samp", "kbd", "var",
        
        # Math Formulas (MathML)
        "math",
        
        # UI / Layout Elements
        "figure", "figcaption",
        
        # Footnote markers and citations (e.g., [1] or ^2)
        "sup", "sub"
    ]
    for element in soup(decompose_targets):
        element.decompose()
        
    # Get text, using spaces to separate element boundaries
    text = soup.get_text(separator=' ')
    
    # Clean up excessive whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
    
    return cleaned_text

def process_epub(epub_path: str) -> list[dict]:
    """
    Main orchestration function for this module.
    Extracts chapters and sanitizes them immediately.
    Returns: list of dicts [{'title': '...', 'text': 'clean narrative text...'}, ...]
    """
    raw_chapters = extract_chapters_from_epub(epub_path)
    clean_chapters = []
    
    for chapter in raw_chapters:
        clean_text = sanitize_html_to_text(chapter['raw_html'])
        # Only keep chapters that actually have text content after cleanup
        if len(clean_text) > 50: 
            clean_chapters.append({
                'title': chapter['title'],
                'text': clean_text
            })
            
    return clean_chapters

if __name__ == "__main__":
    # Simple self-test code block
    print("EPUB Parser module loaded.")
