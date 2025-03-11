import re
from collections import Counter
from functools import lru_cache

import spacy
from spacy.tokens import Doc
from spacy.util import filter_spans

# Precompile regex patterns
WHITESPACE_RE = re.compile(r"\s+")
NON_ALPHANUM_RE = re.compile(r"[^\w\s\-_]+")
LONE_HYPHEN_RE = re.compile(r"\s*-\s*(?!\w)|(?<!\w)\s*-\s*")

# Initialize spaCy with minimal pipeline
nlp = spacy.load("en_core_web_sm", exclude=["lemmatizer", "textcat"])

# Add sentencizer for faster sentence tokenization
sentencizer = nlp.add_pipe("sentencizer")

# spacy chunking pipeline
nlp.add_pipe(
    "spacy_chunks",
    last=True,
    config={
        "chunking_method": "sentence",  # chunking method to use ("sentence" or "token")
        "chunk_size": 15,  # Number of sentences or tokens per chunk
        "overlap": 3,  # Number of overlapping sentences or tokens between chunks
        "truncate": False,  # Whether to remove incomplete chunks at the end
    },
)


@lru_cache(maxsize=10000)
def clean_keyword(kw: str) -> str:
    """Cache cleaned keywords for reuse."""
    # First remove non-alphanumeric chars (except whitespace, hyphens, underscores)
    cleaned = NON_ALPHANUM_RE.sub("", kw).strip()
    # Replace lone hyphens with spaces
    cleaned = LONE_HYPHEN_RE.sub(" ", cleaned)
    # Clean up any resulting multiple spaces
    return WHITESPACE_RE.sub(" ", cleaned).strip()


def extract_keywords(doc: Doc, top_n: int = 25, split_chunks: bool = True) -> list[str]:
    """Optimized keyword extraction with minimal behavior change."""

    excluded_labels = {
        "TIME",  # Times smaller than a day.
        "PERCENT",  # Percentage, including ”%“.
        "QUANTITY",  # Measurements, as of weight or distance.
        "ORDINAL",  # “first”, “second”, etc.
        "CARDINAL",  # Numerals that do not fall under another type.
        "DATE",        # Absolute or relative dates or periods.
        "MONEY",       # Monetary values, including unit.
        # "PERSON",      # People, including fictional.
        # "NORP",        # Nationalities or religious or political groups.
        # "FAC",         # Buildings, airports, highways, bridges, etc.
        # "ORG",         # Companies, agencies, institutions, etc.
        # "GPE",         # Countries, cities, states.
        # "LOC",         # Non-GPE locations, mountain ranges, bodies of water.
        # "PRODUCT",     # Objects, vehicles, foods, etc. (Not services.)
        # "EVENT",       # Named hurricanes, battles, wars, sports events, etc.
        # "WORK_OF_ART", # Titles of books, songs, etc.
        # "LAW",         # Named documents made into laws.
        # "LANGUAGE",    # Any named language.
    }

    # Extract and filter spans in a single pass
    ent_spans = [ent for ent in doc.ents if ent.label_ not in excluded_labels]

    # Add more comprehensive stopword filtering for noun chunks
    chunk_spans = [
        chunk
        for chunk in doc.noun_chunks
        if not chunk.root.is_stop and not all(token.is_stop for token in chunk)
    ]
    all_spans = filter_spans(ent_spans + chunk_spans)

    # Process spans efficiently and filter out spans that are entirely stopwords
    keywords = []
    ent_keywords = []
    seen_texts = set()

    # Convert ent_spans to set for faster lookup
    ent_spans_set = set(ent_spans)

    for span in all_spans:
        # Skip if all tokens in span are stopwords
        if all(token.is_stop for token in span):
            continue

        text = span.text.strip()
        lower_text = text.lower()

        # Skip empty or seen texts
        if not text or lower_text in seen_texts:
            continue

        seen_texts.add(lower_text)
        ent_keywords.append(text) if span in ent_spans_set else keywords.append(text)

    # Normalize keywords by replacing multiple spaces with single space and stripping
    normalized_ent_keywords = [WHITESPACE_RE.sub(" ", kw).strip() for kw in ent_keywords]
    normalized_keywords = [WHITESPACE_RE.sub(" ", kw).strip() for kw in keywords]

    if split_chunks:
        normalized_keywords = [word for kw in normalized_keywords for word in kw.split()]

    # Count frequencies efficiently
    ent_freq = Counter(normalized_ent_keywords)
    freq = Counter(normalized_keywords)

    top_keywords = [kw for kw, _ in ent_freq.most_common(top_n)]
    remaining_slots = max(0, top_n - len(top_keywords))
    top_keywords += [kw for kw, _ in freq.most_common(remaining_slots)]

    return [clean_keyword(kw) for kw in top_keywords]


@lru_cache(maxsize=1000)
def text_to_keywords(
    paragraph: str,
    top_n: int = 25,
    min_keywords: int = 1,
    split_chunks: bool = True,
) -> set[str]:
    """
    Extracts meaningful keywords/phrases from text.

    Example:
        Input: "I like basketball especially Michael Jordan"
        Output: {"basketball", "Michael Jordan"}

    Args:
        paragraph (str): The input text to process
        top_n (int): Number of top keywords to extract per sentence
        min_keywords (int): Minimum number of keywords required
        split_chunks (bool): If True, breaks multi-word noun chunks into individual words

    Returns:
        set[str]: Set of keywords/phrases
    """
    if not paragraph or not paragraph.strip():
        return set()

    doc = nlp(paragraph)
    all_keywords = set()  # Use set to avoid duplicates

    for sent in doc.sents:
        sent_doc = sent.as_doc()

        # Extract keywords
        keywords = extract_keywords(sent_doc, top_n, split_chunks=split_chunks)
        keywords = [kw for kw in keywords if len(kw) > 1]
        if len(keywords) < min_keywords:
            continue

        all_keywords.update(keywords)

    return all_keywords


# def batch_text_to_tsvector_queries(
#     paragraphs: list[str],
#     top_n: int = 10,
#     proximity_n: int = 10,
#     min_keywords: int = 1,
#     n_process: int = 1,
# ) -> list[str]:
#     """
#     Processes multiple paragraphs using nlp.pipe for better performance.

#     Args:
#         paragraphs (list[str]): List of paragraphs to process
#         top_n (int): Number of top keywords to include per paragraph

#     Returns:
#         list[str]: List of tsquery strings
#     """
#     results = []

#     for doc in nlp.pipe(paragraphs, disable=["lemmatizer", "textcat"], n_process=n_process):
#         queries = set()  # Use set to avoid duplicates
#         for sent in doc.sents:
#             sent_doc = sent.as_doc()
#             keywords = extract_keywords(sent_doc, top_n)
#             if len(keywords) < min_keywords:
#                 continue
#             keyword_positions = keyword_matcher.find_matches(sent_doc, keywords)
#             if not keyword_positions:
#                 continue
#             groups = find_proximity_groups(keywords, keyword_positions, proximity_n)
#             # Add each group as a single term to our set
#             for group in groups:
#                 if len(group) > 1:
#                     # Sort by length descending to prioritize longer phrases
#                     sorted_group = sorted(group, key=len, reverse=True)
#                     # For truly proximate multi-word groups, group words
#                     queries.add(" OR ".join(sorted_group))
#                 else:
#                     # For non-proximate words or single words, add them separately
#                     queries.update(group)

#         # Join all terms with " OR "
#         results.append(" OR ".join(queries) if queries else "")

#     return results
