import os
from deep_translator import GoogleTranslator

# Define file paths relative to the script's location (outside scripts folder)
# Assuming the script is in a 'scripts' folder and README.md is one level up
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

readme_path = os.path.join(base_path, 'README.md')
readme_cn_path = os.path.join(base_path, 'README-CN.md')
readme_jp_path = os.path.join(base_path, 'README-JP.md')
readme_fr_path = os.path.join(base_path, 'README-FR.md')

# Language codes for GoogleTranslator
languages = {
    "chinese": "zh-CN",
    "japanese": "ja",
    "french": "fr"
}

# Function to translate content
def translate_content(content, target_lang):
    translator = GoogleTranslator(source='en', target=target_lang)
    return translator.translate(content)

# Read the original README.md content
with open(readme_path, 'r', encoding='utf-8') as f:
    original_content = f.read()

# Translate and save each translation
translations = {
    "chinese": translate_content(original_content, languages["chinese"]),
    "japanese": translate_content(original_content, languages["japanese"]),
    "french": translate_content(original_content, languages["french"]),
}

# Write translated contents to respective files in the same location as README.md
with open(readme_cn_path, 'w', encoding='utf-8') as f:
    f.write(translations["chinese"])

with open(readme_jp_path, 'w', encoding='utf-8') as f:
    f.write(translations["japanese"])

with open(readme_fr_path, 'w', encoding='utf-8') as f:
    f.write(translations["french"])

print("README.md translated to Chinese, Japanese, and French successfully!")