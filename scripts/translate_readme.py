from googletrans import Translator
import os

# Initialize the translator
translator = Translator()

# Load the original README content
with open('README.md', 'r', encoding='utf-8') as readme_file:
    original_content = readme_file.read()

# Define the target languages
languages = {
    'CN': 'zh-cn',  # Chinese
    'JP': 'ja',     # Japanese
    'FR': 'fr',     # French
}

# Translate the content and write to new files
for code, lang in languages.items():
    translated_content = translator.translate(original_content, dest=lang).text

    # Write the translated content to a new file
    with open(f'README-{code}.md', 'w', encoding='utf-8') as translated_file:
        translated_file.write(f'# Translated README in {lang.upper()}\n\n')
        translated_file.write(translated_content)
    
    print(f'Translated README.md to README-{code}.md')

print("Translation complete!")