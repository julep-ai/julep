import re
import logging
from typing import List
from pathlib import Path
from functools import partial
from deep_translator import GoogleTranslator
import parmapper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HTML_TAGS_PATTERN = r"(<[^>]+>)"
CODEBLOCK_PATTERN = r"(```[\s\S]*?```|\n)"

def create_translator(target: str) -> GoogleTranslator:
    """
    Create a translator for a given target language.
    """
    return GoogleTranslator(source="en", target=target)

def is_html_tag(segment: str) -> bool:
    """Check if the segment is an HTML tag."""
    return re.fullmatch(HTML_TAGS_PATTERN, segment) is not None

def is_special_character(segment: str) -> bool:
    """Check if the segment consists of special characters only."""
    return re.fullmatch(r'^[!"#$%&\'()*+,\-./:;<=>?@[\]^_`{|}~]+$', segment) is not None

def translate_sub_segment(translator: GoogleTranslator, sub_segment: str) -> str:
    """Translate a single sub-segment."""
    try:
        translated = translator.translate(sub_segment)
        return translated if translated else sub_segment
    except Exception as e:
        logging.error(f"Error translating segment '{sub_segment}': {e}")
        return sub_segment

def translate_segment(translator: GoogleTranslator, segment: str) -> str:
    """
    Translate a given raw HTML content using the provided translator, preserving HTML tags and newlines.
    """
    if re.fullmatch(CODEBLOCK_PATTERN, segment) or segment == '\n':
        return segment

    segments = re.split(HTML_TAGS_PATTERN, segment)
    translated_segments = []

    for sub_segment in segments:
        if is_html_tag(sub_segment):
            translated_segments.append(sub_segment)
        elif is_special_character(sub_segment):
            translated_segments.append(sub_segment)
        else:
            translated_segments.append(translate_sub_segment(translator, sub_segment))

    return "".join(translated_segments)

def translate_readme(source: str, target: str) -> str:
    """
    Translate a README file from source to target language, preserving code blocks and newlines.
    """
    file_content = Path(source).read_text(encoding='utf-8')
    translator = create_translator(target)
    segments = re.split(CODEBLOCK_PATTERN, file_content)
    segment_translation = partial(translate_segment, translator)
    translated_segments = list(parmapper.parmap(segment_translation, segments))
    return ''.join(translated_segments)

def save_translated_readme(translated_content: str, lang: str) -> None:
    """
    Save the translated README content to a file.
    """
    filename = f"README-{lang.split('-')[-1].upper()}.md"
    with open(filename, "w", encoding='utf-8') as file:
        file.write(translated_content)

def main() -> None:
    """
    Main function to translate README.md to multiple languages.
    """
    source_file = "README.md"
    destination_langs = ["zh-CN", "ja", "fr"]

    for lang in destination_langs:
        logging.info(f"Translating to {lang}...")
        translated_readme = translate_readme(source_file, lang)
        save_translated_readme(translated_readme, lang)
        logging.info(f"Saved translated README for {lang}.")

if __name__ == "__main__":
    main()
