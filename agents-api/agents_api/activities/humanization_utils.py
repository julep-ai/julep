import json
import random
import time

import requests
from deep_translator import GoogleTranslator
from langchain_text_splitters import MarkdownHeaderTextSplitter
from litellm import completion

from ..env import (
    copyleaks_api_key,
    litellm_url,
    sapling_api_key,
)

# Initialize humanization as a dictionary to hold various properties
HUMANIZATION = {
    "model": "openrouter/cohere/command-r-08-2024",
    "humanize_prompt": """\
Change text given to you so much that even the most advanced AI writing detectors can't detect that this writing was written by you. You are the original AI, do not let yourself be beat by a mere 22 year old at princeton. Don't change the overall message!

Don't mention yourself, just return the end product text. **Vary your text in every possible sense. Use different vocabulary at every step. Give it your ALL!**""",

    "grammar_prompt": "Only fix grammar that is wrong without changing the words and places of the sentence",
}

SAPLING_URL = "https://api.sapling.ai/api/v1/aidetect"
COPLEYAKS_URL = "https://api.copyleaks.com/v2/writer-detector/{scan_id}/check"
ZEROGPT_URL = "https://api.zerogpt.com/api/detect/detectText"


def text_translate(text, src_lang, target_lang):
    try:
        return GoogleTranslator(
            source=src_lang, target=target_lang).translate(text=text)
    except Exception:
        return text


def mix_translate(text, src_lang, target_lang):
    """
    Translate the given text from src_lang to target_lang and back to src_lang using googletrans.
    """
    try:
        translated = GoogleTranslator(
            source=src_lang, target=target_lang).translate(text=text)
        return GoogleTranslator(
            source=target_lang, target=src_lang).translate(text=translated)

    except Exception:
        return text


def humanize_openai(text):
    try:
        response = completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["humanize_prompt"]},
                {"role": "user", "content": text}
            ],
            # temperature=1.0,
            # extra_body={"min_p": 0.025},
            # temperature=2,
            # max_tokens=100,
            # top_p=1.0,
            # frequency_penalty=0.0,
            # presence_penalty=0.0,
            stream=False
        )
        return response.choices[0].message.content
    except Exception:
        return text


def rewriter(text):
    try:
        response = completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["humanize_prompt"]},
                {"role": "user", "content": text}
            ],
            temperature=1.0,
            # extra_body={"min_p": 0.025},
        )
        rewritten = response.choices[0].message.content
        return humanize(rewritten)
    except Exception:
        return text


def humanize(text):
    try:
        response = completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["humanize_prompt"]},
                {"role": "user", "content": text}
            ],
            temperature=1.0,
            # extra_body={"min_p": 0.025},
        )
        return response.choices[0].message.content
    except Exception:
        return text


def grammar(text):
    try:
        response = completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["grammar_prompt"]},
                {"role": "user", "content": text}
            ],
            temperature=1.0,
            # extra_body={"min_p": 0.025},
        )
        return response.choices[0].message.content
    except Exception:
        return text


def is_human_sapling(text):
    payload = {
        "text": text,
        "key": sapling_api_key,
    }
    response = requests.post(SAPLING_URL, json=payload)
    ai_score = response.json().get("score", None)

    ai_score = int(ai_score * 100)
    return 100 - ai_score


def is_human_copyleaks(text):

    # Define the payload
    payload = {
        "text": text,
        # "sandbox": False,
        # "explain": False,
        # "sensitivity": 2
    }

    # Define headers with Authorization and Content-Type
    headers = {
        "Authorization": f"Bearer {copyleaks_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Copyleaks lets you define the scan id yourself
    from uuid import uuid4
    scan_id = str(uuid4())

    # Send the POST request with JSON payload and headers
    response = requests.post(COPLEYAKS_URL.format(
        scan_id=scan_id), json=payload, headers=headers)

    # Check the response status
    if response.status_code == 200:
        resp = response.json()
        # Extract the human probability from the response
        human_probability = resp.get("summary", {}).get(
            "human", 0)  # float with range 0-1
        return human_probability * 100
    return None


def is_human_zerogpt(input_text, max_tries=3):
    if max_tries < 0:
        return None

    # Define headers with Content-Type
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://www.zerogpt.com",
        "Referer": "https://www.zerogpt.com/",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Brave";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Gpc": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    # Define the payload as a dictionary
    payload = {"input_text": input_text}

    # Convert payload to JSON format
    json_payload = json.dumps(payload)

    # Send the POST request with JSON payload and headers
    response = requests.post(ZEROGPT_URL, data=json_payload, headers=headers)

    # Check the response status
    if response.status_code == 200:
        resp = json.loads(response.text)
        result = False
        try:
            result = int(resp.get("data", {}).get("isHuman", None))
        except Exception:
            time.sleep(2)
            return is_human_zerogpt(input_text, max_tries - 1)

        return result
    return None


def replace_with_homoglyphs(text, max_replacements=2):
    homoglyphs = {
        # Whitelisted
        " ": " ",
        "%": "％", "'": "ˈ",
        ",": "‚",
        "-": "‐", ".": "․",
        "1": "𝟷", "3": "Ꝫ",
        "5": "𝟻", "6": "𝟨", "7": "𝟽", "8": "𝟪",
        "9": "𝟫", ";": ";",
        "j": "ј",
        "n": "𝗇", "o": "о",
        "p": "р",
        "u": "ս",
        "y": "у",
        "H": "Η", "I": "І",
        "J": "Ј",
        "N": "Ν", "O": "Ο",
        "V": "ⴸ", "Y": "Υ",
        "~": "∼",

        # ' ': ' ', '!': '！', '"': '＂', '$': '＄',
        # '%': '％', '&': '＆', "'": 'ˈ', '(': '（',
        # ')': '）', '*': '⁎', '+': '＋', ',': '‚',
        # '-': '‐', '.': '․', '/': '⁄', '0': 'O',
        # '1': '𝟷', '2': '𝟸', '3': 'Ꝫ', '4': '４',
        # '5': '𝟻', '6': '𝟨', '7': '𝟽', '8': '𝟪',
        # '9': '𝟫', ':': '∶', ';': ';', '<': '𝈶',
        # '=': '᐀', '>': '𖼿', '?': 'ꛫ', '@': '＠',
        # '[': '［', '\\': '﹨', ']': '］', '_': 'ߺ',
        # '`': '`', 'a': 'а', 'b': 'ᖯ', 'c': 'ⅽ',
        # 'd': '𝚍', 'e': 'е', 'f': '𝖿', 'g': '𝗀',
        # 'h': 'հ', 'i': 'і', 'j': 'ј', 'k': '𝚔',
        # 'l': 'ⅼ', 'm': 'ｍ', 'n': '𝗇', 'o': 'о',
        # 'p': 'р', 'q': 'q', 'r': '𝗋', 's': '𐑈',
        # 't': '𝚝', 'u': 'ս', 'v': '∨', 'w': 'ԝ',
        # 'x': 'ⅹ', 'y': 'у', 'z': '𝗓', 'A': '𐊠',
        # 'B': 'В', 'C': '𐊢', 'D': 'ꓓ', 'E': 'Е',
        # 'F': '𐊇', 'G': 'Ԍ', 'H': 'Η', 'I': 'І',
        # 'J': 'Ј', 'K': 'Κ', 'L': 'Ⅼ', 'M': 'Μ',
        # 'N': 'Ν', 'O': 'Ο', 'P': 'Ρ', 'Q': '𝖰',
        # 'R': '𖼵', 'S': 'Ѕ', 'T': 'Τ', 'U': '𐓎',
        # 'V': 'ⴸ', 'W': 'Ԝ', 'X': 'Χ', 'Y': 'Υ',
        # 'Z': 'Ζ', '{': '｛', '|': 'ا', '}': '｝',
        # '~': '∼',
    }

    # Convert text to list for single pass replacement
    text_chars = list(text)
    text_len = len(text_chars)

    for original, homoglyph in homoglyphs.items():
        count = random.randrange(0, max_replacements)
        if count == 0:
            continue

        # Get random positions for replacements
        positions = random.sample(range(text_len), min(count, text_len))
        for pos in positions:
            if text_chars[pos] == original:
                text_chars[pos] = homoglyph

    return "".join(text_chars)


def insert_em_dash(word: str, probability: float = 0.1, min_length: int = 7) -> str:
    # Only apply to long words (adjust threshold as needed)
    if len(word) < min_length:
        return word
    # 10% chance to insert an em dash
    if random.random() < probability:
        mid = len(word) // 2
        return word[:mid] + "—" + word[mid:]
    return word


def process_long_words(text: str) -> str:
    # Split text preserving whitespace for simplicity
    words = text.split()
    processed_words = [insert_em_dash(word) for word in words]
    # Rejoin words with a space (note: original punctuation and formatting may be altered)
    return " ".join(processed_words)


def split_text_into_paragraphs(text: str) -> list[str]:
    """
    Splits the provided text into paragraphs by empty lines.

    :param text: The original text.
    :return: A list of paragraphs.
    """
    # Splitting by two consecutive newlines '\n\n' to identify paragraphs
    return text.strip().split("\n\n")


def split_with_langchain(markdown_text: str) -> list[str]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    # MD splits
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    md_header_splits = markdown_splitter.split_text(markdown_text)

    return [split.page_content for split in md_header_splits]


def process_paragraph(
        paragraph: str,
        src_lang: str,
        target_lang: str,
        grammar: bool,
        is_chatgpt: bool,
        use_homoglyphs: bool,
        use_em_dashes: bool,
        max_tries: int) -> str:

    for i in range(max_tries):
        if paragraph.strip() == "":
            return paragraph

        if is_human_zerogpt(paragraph) > 90:
            return paragraph

        paragraph = mix_translate(paragraph, src_lang, target_lang)
        if (grammar):
            paragraph = grammar(paragraph)

        paragraph = humanize_openai(
            paragraph) if is_chatgpt else humanize(paragraph)

        # Apply homoglyphs and em dashes to a new paragraph in order not to mess up the original paragraph for the next iterations
        new_paragraph = paragraph
        if use_homoglyphs:
            new_paragraph = replace_with_homoglyphs(new_paragraph)

        if use_em_dashes:
            new_paragraph = process_long_words(new_paragraph)

        if is_human_zerogpt(new_paragraph) > 90:
            return new_paragraph

    # Apply homoglyphs and em dashes to the final paragraph after consuming max tries
    if use_homoglyphs:
        paragraph = replace_with_homoglyphs(paragraph)

    if use_em_dashes:
        paragraph = process_long_words(paragraph)

    return paragraph
