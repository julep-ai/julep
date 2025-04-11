import json
import random
import time

import litellm
import requests
from deep_translator import GoogleTranslator
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

from ...env import (
    desklib_url,
    litellm_master_key,
    litellm_url,
    sapling_api_key,
    sapling_url,
    zerogpt_url,
)

# Initialize humanization as a dictionary to hold various properties
HUMANIZATION = {
    "model": "openai/cerebras/llama-3.3-70b",
    "humanize_prompt": """\
    Rewrite the following text to make it more natural and human-like while preserving the core message. Follow these guidelines:

1. Maintain the original meaning and key points
2. Vary sentence structure (mix simple, compound, and complex sentences)
3. Use natural language patterns:
   - Include occasional filler words (well, actually, you know)
   - Add subtle imperfections (parenthetical thoughts, self-corrections)
   - Employ informal transitions where appropriate
4. Incorporate personal voice:
   - Use contractions naturally
   - Add conversational elements
   - Vary vocabulary complexity
5. Keep paragraphing and flow natural
6. Avoid overly perfect grammar or clinical language

Notes:
- The text you are rewriting has been translated from one language to another, and back to English.
- The rewritten text should be in markdown format (don't add headings unless they are already present).
- If you see spaces before or after double stars, you should remove them.
- If you see headings without capitalized text, you should capitalize them.


Return only the rewritten text without explanations or meta-commentary.""",
    "grammar_prompt": "Only fix grammar that is wrong without changing the words and places of the sentence",
}


def text_translate(text, src_lang, target_lang):
    try:
        return GoogleTranslator(source=src_lang, target=target_lang).translate(text=text)
    except Exception:
        return text


def mix_translate(text, src_lang, target_lang):
    """
    Translate the given text from src_lang to target_lang and back to src_lang using googletrans.
    """
    try:
        translated = GoogleTranslator(source=src_lang, target=target_lang).translate(text=text)
        return GoogleTranslator(source=target_lang, target=src_lang).translate(text=translated)

    except Exception:
        return text


def humanize_llm(text: str) -> str:
    try:
        response = litellm.completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["humanize_prompt"]},
                {"role": "user", "content": text},
            ],
            temperature=1.0,
            api_key=litellm_master_key,
        )
        return response.choices[0].message.content
    except Exception as e:
        msg = "Error humanizing text with an llm: "
        raise Exception(msg) from e


def grammar(text):
    try:
        response = litellm.completion(
            model=HUMANIZATION["model"],
            base_url=litellm_url,
            messages=[
                {"role": "system", "content": HUMANIZATION["grammar_prompt"]},
                {"role": "user", "content": text},
            ],
            temperature=1.0,
            api_key=litellm_master_key,
            # extra_body={"min_p": 0.025},
        )
        return response.choices[0].message.content
    except Exception:
        return text


def is_human_desklib(text: str) -> float:
    try:
        payload = {
            "text": text,
        }
        response = requests.post(desklib_url, json=payload)

        response.raise_for_status()

        ai_score = response.json().get("probability")

        if ai_score is None:
            msg = "'probability' key not found in response: "
            raise Exception(msg, response.json())

        human_score = 1 - ai_score

        # desklib returns a score between 0 and 1, we want to return a percentage
        return human_score * 100
    except Exception as e:
        msg = "Error getting human score from desklib"
        raise Exception(msg) from e


def is_human_sapling(text):
    try:
        payload = {
            "text": text,
            "key": sapling_api_key,
        }
        response = requests.post(sapling_url, json=payload)
        ai_score = response.json().get("score", None)

        # sapling returns a an ai score between 0 and 1, we want to return a human_score percentage
        return 100 - int(ai_score * 100)
    except Exception as e:
        msg = "Error getting human score from sapling"
        raise Exception(msg) from e


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
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }
    # Define the payload as a dictionary
    payload = {"input_text": input_text}

    # Convert payload to JSON format
    json_payload = json.dumps(payload)

    # Send the POST request with JSON payload and headers
    response = requests.post(zerogpt_url, data=json_payload, headers=headers)

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
        "%": "％",
        "'": "ˈ",
        ",": "‚",
        "-": "‐",
        ".": "․",
        "1": "𝟷",
        "3": "Ꝫ",
        "5": "𝟻",
        "6": "𝟨",
        "7": "𝟽",
        "8": "𝟪",
        "9": "𝟫",
        ";": ";",
        "j": "ј",
        "n": "𝗇",
        "o": "о",
        "p": "р",
        "u": "ս",
        "y": "у",
        "H": "Η",
        "I": "І",
        "J": "Ј",
        "N": "Ν",
        "O": "Ο",
        "V": "ⴸ",
        "Y": "Υ",
        "~": "∼",
        "q": "q",
        "e": "е",
        "a": "а",
        "b": "ᖯ",
        "c": "ⅽ",
        "i": "і",
        "k": "𝚔",
        "g": "𝗀",
        "A": "𐊠",
        "B": "В",
        "C": "𐊢",
        "D": "ꓓ",
        "E": "Е",
        "F": "𐊇",
        "G": "Ԍ",
        "K": "Κ",
        "L": "Ⅼ",
        "M": "Μ",
        "P": "Ρ",
        "Q": "𝖰",
        "R": "𖼵",
        "S": "Ѕ",
        "T": "Τ",
        "U": "𐓎",
        "W": "Ԝ",
        "X": "Χ",
        "Z": "Ζ",
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


def split_with_langchain(markdown_text: str) -> list[Document]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    # MD splits
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=True,
    )
    return markdown_splitter.split_text(markdown_text)


def reassemble_markdown(splits: list[Document]) -> str:
    assembled_text = []

    for doc in splits:
        # Get the header level from metadata
        header_level = None
        header_content = None
        for key, value in doc.metadata.items():
            if key.startswith("Header "):
                header_level = int(key.split(" ")[1])
                header_content = value
                break

        # Add header with appropriate number of # symbols
        if header_level and header_content:
            header_line = f"{'#' * header_level} {header_content}\n\n"
            assembled_text.append(header_line)

        # Add the content
        assembled_text.append(f"{doc.page_content}\n---\n")

    return "".join(assembled_text).strip()


def humanize_paragraph(
    paragraph: str,
    threshold: float,
    src_lang: str,
    target_lang: str,
    grammar_check: bool,
    use_homoglyphs: bool,
    use_em_dashes: bool,
    max_tries: int,
) -> str:
    for i in range(max_tries):
        if paragraph.strip() == "":
            return paragraph

        if is_human_desklib(paragraph) > threshold:
            return paragraph

        paragraph = mix_translate(paragraph, src_lang, target_lang)
        if grammar_check:
            paragraph = grammar(paragraph)

        paragraph = humanize_llm(paragraph)

    # Apply homoglyphs and em dashes to a new paragraph in order not to mess up the original paragraph for the next iterations
    new_paragraph = paragraph
    if use_homoglyphs:
        new_paragraph = replace_with_homoglyphs(new_paragraph)

    if use_em_dashes:
        new_paragraph = process_long_words(new_paragraph)

    if is_human_desklib(new_paragraph) > threshold:
        return new_paragraph

    # Apply homoglyphs and em dashes to the final paragraph after consuming max tries
    if use_homoglyphs:
        paragraph = replace_with_homoglyphs(paragraph)

    if use_em_dashes:
        paragraph = process_long_words(paragraph)

    return paragraph
