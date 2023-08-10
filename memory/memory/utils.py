from datetime import datetime, timezone, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from keybert import KeyBERT
from keyphrase_vectorizers import KeyphraseCountVectorizer
from transformers import AutoTokenizer

from .types import ChatMLMessage, ChatML

tokenizer_id = "julep-ai/samantha-33b"
tokenizer = AutoTokenizer.from_pretrained(tokenizer_id, use_fast=False)

vectorizer = KeyphraseCountVectorizer(pos_pattern="<N.*>")
kw_model = KeyBERT(model="all-MiniLM-L6-v2")


@lru_cache
def count_tokens(prompt: str):
    tokens = tokenizer.encode(prompt)
    return len(tokens)


def message_role_to_prefix(message: ChatMLMessage) -> str:
    match message:
        case {"role": "system", "name": name, **_rest}:
            return name
        case {"role": "user", "name": name, **_rest}:
            return f"person ({name})" if name else "person"
        case {"role": "assistant", "name": name, **_rest}:
            return f"me ({name})" if name else "me"


def to_prompt(
    messages: ChatML,
    suffix: str,
    bos: str = "<|section|>",
    eos: str = "<|endsection|>",
) -> str:
    # Input format:
    # [
    #     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
    #     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
    #     {"role": "user", "name": "Diwank", "content": "Hey!"},
    # ]

    # Output format:
    #
    # <|section|>situation
    # I am talking to Diwank<|endsection|>
    # <|section|>me (Samantha)
    # Hey Diwank<|endsection|>
    # <|section|>person (Diwank)
    # Hey<|endsection|>
    # <|section|>me (Samantha)\n

    prompt = "\n".join(
        [
            f"{bos}{message_role_to_prefix(message)}\n{message['content']}{eos}"
            for message in messages
        ]
    )

    return prompt + suffix


def get_aligned_datetime(
    time: datetime,
    align_by: timedelta = timedelta(minutes=30),
    tz: timezone = timezone.utc,
) -> datetime:
    time = time.astimezone(tz).replace(tzinfo=None)
    r = (datetime.min - time) % align_by
    result = (
        time - (time - datetime.min) % align_by
        if r.seconds > align_by.seconds / 2
        else time + r
    )

    return result.replace(tzinfo=tz)


def get_human_date_time(tz: timezone = ZoneInfo("Asia/Kolkata")) -> str:
    """To get the current date and time"""
    dt = get_aligned_datetime(datetime.now(), tz=tz)

    return dt.strftime("%I:%M%p on %A, %b %d %Y")


def truncate(
    chatml: ChatML,
    max_tokens: int = 1500,
    keep_when=lambda x, i: x["role"] == "system" or i == 0,
    suffix: str = "<|section|>me (Samantha)\n",
) -> ChatML:
    # Add indices to chatml
    chatml_with_idx = list(enumerate(chatml))

    # Keep all messages that pass the keep_when function
    chatml_to_keep = [c for c in chatml_with_idx if keep_when(c[1], c[0])]

    # Calculate budget
    budget = (
        max_tokens
        - sum([count_tokens(to_prompt([c[1]], suffix="")) for c in chatml_to_keep])
        - count_tokens(suffix)
    )

    assert budget > 0, "keep_when(...) messages have already exhausted token budget"

    # Start going through messages in reverse order and keep them if they fit
    remaining = chatml_with_idx[:]
    for i, c in reversed(remaining):
        # This message has already been kept
        if keep_when(c, i):
            continue

        c_len = count_tokens(to_prompt([c], suffix=""))

        # This message is too long to keep
        if budget < c_len:
            break

        # Keep this message
        budget -= c_len
        chatml_to_keep.append((i, c))

    # Sort all kept messages by index and remove index
    sorted_kept = sorted(chatml_to_keep, key=lambda x: x[0])
    truncated = [c for _, c in sorted_kept]

    return truncated


def extract_keywords(doc, top_n: int = 5, **kwargs) -> list[tuple[str, float]]:
    opts = {
        "top_n": top_n,
        "stop_words": "english",
        "vectorizer": vectorizer,
        "use_mmr": True,
        "diversity": 0.7,
        **kwargs,
    }

    keywords = kw_model.extract_keywords(doc, **opts)
    return keywords
