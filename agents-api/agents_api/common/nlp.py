import re
from collections import Counter, defaultdict
from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc
from spacy.util import filter_spans

# Precompile regex patterns
WHITESPACE_RE = re.compile(r"\s+")
NON_ALPHANUM_RE = re.compile(r"[^\w\s\-_]+")

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


# Singleton PhraseMatcher for better performance
class KeywordMatcher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            cls._instance.batch_size = 1000  # Adjust based on memory constraints
            cls._instance.patterns_cache = {}
        return cls._instance

    @lru_cache(maxsize=10000)
    def _create_pattern(self, text: str) -> Doc:
        return nlp.make_doc(text)

    def find_matches(self, doc: Doc, keywords: list[str]) -> dict[str, list[int]]:
        """Batch process keywords for better performance."""
        keyword_positions = defaultdict(list)

        # Process keywords in batches to avoid memory issues
        for i in range(0, len(keywords), self.batch_size):
            batch = keywords[i : i + self.batch_size]
            patterns = [self._create_pattern(kw) for kw in batch]

            # Clear previous patterns and add new batch
            if "KEYWORDS" in self.matcher:
                self.matcher.remove("KEYWORDS")
            self.matcher.add("KEYWORDS", patterns)

            # Find matches for this batch
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span_text = doc[start:end].text
                normalized = WHITESPACE_RE.sub(" ", span_text).lower().strip()
                keyword_positions[normalized].append(start)

        return keyword_positions


# Initialize global matcher
keyword_matcher = KeywordMatcher()


@lru_cache(maxsize=10000)
def clean_keyword(kw: str) -> str:
    """Cache cleaned keywords for reuse."""
    return NON_ALPHANUM_RE.sub("", kw).strip()


def extract_keywords(doc: Doc, top_n: int = 10, clean: bool = True) -> list[str]:
    """Optimized keyword extraction with minimal behavior change."""
    excluded_labels = {
        "DATE",
        "TIME",
        "PERCENT",
        "MONEY",
        "QUANTITY",
        "ORDINAL",
        "CARDINAL",
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
    seen_texts = set()

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
        keywords.append(text)

    # Normalize keywords by replacing multiple spaces with single space and stripping
    normalized_keywords = [WHITESPACE_RE.sub(" ", kw).strip() for kw in keywords]

    # Count frequencies efficiently
    freq = Counter(normalized_keywords)
    top_keywords = [kw for kw, _ in freq.most_common(top_n)]

    if clean:
        return [clean_keyword(kw) for kw in top_keywords]
    return top_keywords


def find_proximity_groups(
    keywords: list[str], keyword_positions: dict[str, list[int]], n: int = 10
) -> list[set[str]]:
    """Optimized proximity grouping using sorted positions."""
    # Early return for single or no keywords
    if len(keywords) <= 1:
        return [{kw} for kw in keywords]

    # Create flat list of positions for efficient processing
    positions: list[tuple[int, str]] = [
        (pos, kw) for kw in keywords for pos in keyword_positions[kw]
    ]

    # Sort positions once
    positions.sort()

    # Initialize Union-Find with path compression and union by rank
    parent = {kw: kw for kw in keywords}
    rank = dict.fromkeys(keywords, 0)

    def find(u: str) -> str:
        if parent[u] != u:
            parent[u] = find(parent[u])
        return parent[u]

    def union(u: str, v: str) -> None:
        u_root, v_root = find(u), find(v)
        if u_root != v_root:
            if rank[u_root] < rank[v_root]:
                u_root, v_root = v_root, u_root
            parent[v_root] = u_root
            if rank[u_root] == rank[v_root]:
                rank[u_root] += 1

    # Use sliding window for proximity checking
    window = []
    for pos, kw in positions:
        # Remove positions outside window
        while window and pos - window[0][0] > n:
            window.pop(0)

        # Union with all keywords in window
        for _, w_kw in window:
            union(kw, w_kw)

        window.append((pos, kw))

    # Group keywords efficiently
    groups = defaultdict(set)
    for kw in keywords:
        root = find(kw)
        groups[root].add(kw)

    return list(groups.values())


@lru_cache(maxsize=1000)
def text_to_tsvector_query(
    paragraph: str, top_n: int = 10, proximity_n: int = 10, min_keywords: int = 1
) -> str:
    """
    Extracts meaningful keywords/phrases from text and joins them with OR.

    Example:
        Input: "I like basketball especially Michael Jordan"
        Output: "basketball OR Michael Jordan"

    Args:
        paragraph (str): The input text to process
        top_n (int): Number of top keywords to extract per sentence
        proximity_n (int): The proximity window for grouping related keywords
        min_keywords (int): Minimum number of keywords required

    Returns:
        str: Keywords/phrases joined by OR
    """
    if not paragraph or not paragraph.strip():
        return ""

    doc = nlp(paragraph)
    queries = set()  # Use set to avoid duplicates

    for sent in doc.sents:
        sent_doc = sent.as_doc()

        # Extract keywords
        keywords = extract_keywords(sent_doc, top_n)
        if len(keywords) < min_keywords:
            continue

        # Find keyword positions
        keyword_positions = keyword_matcher.find_matches(sent_doc, keywords)
        if not keyword_positions:
            continue

        # Group related keywords by proximity
        groups = find_proximity_groups(keywords, keyword_positions, proximity_n)

        # Add each group as a single term to our set
        for group in groups:
            if len(group) > 1:
                # Sort by length descending to prioritize longer phrases
                sorted_group = sorted(group, key=len, reverse=True)
                # For truly proximate multi-word groups, group words
                queries.add(" OR ".join(sorted_group))
            else:
                # For non-proximate words or single words, add them separately
                queries.update(group)

    # Join all terms with " OR "
    return " OR ".join(queries) if queries else ""


def batch_text_to_tsvector_queries(
    paragraphs: list[str],
    top_n: int = 10,
    proximity_n: int = 10,
    min_keywords: int = 1,
    n_process: int = 1,
) -> list[str]:
    """
    Processes multiple paragraphs using nlp.pipe for better performance.

    Args:
        paragraphs (list[str]): List of paragraphs to process
        top_n (int): Number of top keywords to include per paragraph

    Returns:
        list[str]: List of tsquery strings
    """
    results = []

    for doc in nlp.pipe(paragraphs, disable=["lemmatizer", "textcat"], n_process=n_process):
        queries = set()  # Use set to avoid duplicates
        for sent in doc.sents:
            sent_doc = sent.as_doc()
            keywords = extract_keywords(sent_doc, top_n)
            if len(keywords) < min_keywords:
                continue
            keyword_positions = keyword_matcher.find_matches(sent_doc, keywords)
            if not keyword_positions:
                continue
            groups = find_proximity_groups(keywords, keyword_positions, proximity_n)
            # Add each group as a single term to our set
            for group in groups:
                if len(group) > 1:
                    # Sort by length descending to prioritize longer phrases
                    sorted_group = sorted(group, key=len, reverse=True)
                    # For truly proximate multi-word groups, group words
                    queries.add(" OR ".join(sorted_group))
                else:
                    # For non-proximate words or single words, add them separately
                    queries.update(group)

        # Join all terms with " OR "
        results.append(" OR ".join(queries) if queries else "")

    return results
