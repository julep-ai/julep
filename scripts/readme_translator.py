from deep_translator import GoogleTranslator
from pathlib import Path
import re
from typing import List

def create_translator(target: str) -> GoogleTranslator:
    """
    Create a translator for a given target language.
    """
    return GoogleTranslator(source="en", target=target)

def translate_raw_html(translator: GoogleTranslator, html_content: str) -> str:
    """
    Translate a given raw html content using the provided translator, preserving HTML tags and newlines.
    """
    html_tags_pattern = r"(<[^>]+>)"
    segments = re.split(html_tags_pattern, html_content)

    translated_segments = []
    for segment in segments:
        if re.fullmatch(html_tags_pattern, segment):
            translated_segments.append(segment)
        else:
            try:
                if re.fullmatch(r'^[!"#$%&\'()*+,\-./:;<=>?@[\]^_`{|}~]+$', segment):
                    translated_segments.append(segment)
                    continue
                translated = translator.translate(segment)
                translated_segments.append(translated if translated else segment)
            except Exception as e:
                print(f"Error translating segment '{segment}': {e}")
                translated_segments.append(segment)
    return "".join(translated_segments)

def translate_readme(source: str, target: str) -> str:
    """
    Translate a README file from source to target language, preserving code blocks and newlines.
    """
    file_content = Path(source).read_text(encoding='utf-8')
    translator = create_translator(target)
    code_block_pattern = r"(```[\s\S]*?```|\n)"
    segments = re.split(code_block_pattern, file_content)
    
    translated_segments = []
    for segment in segments:
        if re.fullmatch(code_block_pattern, segment) or segment == '\n':
            translated_segments.append(segment)
        else:
            translated_segments.append(translate_raw_html(translator, segment))
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