import os
from markdown_it import MarkdownIt
from markdown_it.token import Token
from deep_translator import GoogleTranslator

# Define file paths relative to the script's location (outside scripts folder)
# Assuming the script is in a 'scripts' folder and README.md is one level up
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

readme_path = os.path.join(base_path, 'README.md')
readme_cn_path = os.path.join(base_path, 'README-CN.md')
readme_jp_path = os.path.join(base_path, 'README-JP.md')
readme_fr_path = os.path.join(base_path, 'README-FR.md')

# Function to split text into chunks of 5000 characters or less
def split_text(text, max_len=5000):
    return [text[i:i + max_len] for i in range(0, len(text), max_len)]

def is_text_token(token: Token) -> bool:
    # Check if the token is a text token that needs translation
    return token.type == 'inline' and all(child.type == 'text' for child in token.children)

# Function to translate the text, handling the 5000 character limit
def translate_text(text, lang):
    # Translate the text in Markdown while preserving other Markdown elements
	md = MarkdownIt()
	translator = GoogleTranslator(source='en', target=lang)
	translated_text = ''

    # Split the text into chunks if it's longer than 5000 characters
	chunks = split_text(text)
    
	# Translate each chunk and combine the results
	for chunk in chunks:
		tokens = md.parse(chunk)
		for token in tokens:
			if is_text_token(token) and token.content.strip():
				try:
					translated_text += translator.translate(token.content) or token.content
				except Exception as e:
					print(f"Error translating '{token.content}': {e}")
					translated_text += token.content
			else:
				translated_text += token.content
    
	return translated_text

# Read the README file
with open(readme_path, 'r', encoding='utf-8') as file:
    original_content = file.read()

# Translate to different languages
languages = {
    'zh-CN': readme_cn_path,  # Chinese
    'ja': readme_jp_path,        # Japanese
    'fr': readme_fr_path         # French
}

# Translate and write the translated content to corresponding files
for lang, filename in languages.items():
    translated_content = translate_text(original_content, lang)
    with open(f'{filename}', 'w', encoding='utf-8') as output_file:
        output_file.write(translated_content)

print("README.md translated to Chinese, Japanese, and French successfully!")