# Audiobook TTS Converter

A command-line tool that converts EPUB files into M4B audiobooks using on-device Text-to-Speech (TTS) models.

## Features

* Converts entire EPUB books into a single M4B audiobook file with metadata.
* Uses the Kokoro TTS engine by default for high-speed, local generation.
* Supports XTTSv2 as an alternative TTS engine.
* Voice Blending: Combine multiple Kokoro voices using mathematical formulas (e.g., bm_lewis*0.5+bm_george*0.5).
* EPUB Parsing: Automatically extracts text and sanitizes HTML.
* Smart Filtering: Skips over code blocks, tables, math formulas, and other structural elements that do not narrate well.
* Pacing: Injects natural silence between paragraphs for better listening.
* Offline Execution: Processes everything entirely on your local machine.

## Usage

Basic usage:
python main.py --epub_path /path/to/book.epub

Specify a different output directory:
python main.py --epub_path /path/to/book.epub --output ./my_audiobooks/

Blend multiple voices:
python main.py --epub_path /path/to/book.epub --engine blend --voice "bm_lewis*0.6+bm_george*0.4"

Use XTTSv2 engine:
python main.py --epub_path /path/to/book.epub --engine xtts --voice "default"
