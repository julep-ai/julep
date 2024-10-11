import re
from typing import List
from pathlib import Path
from functools import partial
from deep_translator import GoogleTranslator
import parmapper

HTML_TAGS_PATTERN = r"(<[^>]+>)"
CODEBLOCK_PATTERN = r"(```[\s\S]*?```|\n)"

def create_translator(target: str) -> GoogleTranslator:
    """
    Create a translator for a given target language.
    """
    return GoogleTranslator(source="en", target=target)

def translate_segment(translator: GoogleTranslator, segment: str) -> str:
    """
    Translate a given raw HTML content using the provided translator, preserving HTML tags and newlines.
    """
    if re.fullmatch(CODEBLOCK_PATTERN, segment) or segment == '\n':
        return segment

    segments = re.split(HTML_TAGS_PATTERN, segment)
    translated_segments = []

    for sub_segment in segments:
        if re.fullmatch(HTML_TAGS_PATTERN, sub_segment):
            translated_segments.append(sub_segment)
        else:
            try:
                if re.fullmatch(r'^[!"#$%&\'()*+,\-./:;<=>?@[\]^_`{|}~]+$', sub_segment):
                    translated_segments.append(sub_segment)
                    continue

                translated = translator.translate(sub_segment)
                translated_segments.append(translated if translated else sub_segment)
            except Exception as e:
                print(f"Error translating segment '{sub_segment}': {e}")
                translated_segments.append(sub_segment)

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
        translated_readme = translate_readme(source_file, lang)
        save_translated_readme(translated_readme, lang)

if __name__ == "__main__":
    main()