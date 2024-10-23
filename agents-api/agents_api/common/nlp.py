import re
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Dict, List, Set, Tuple

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc
from spacy.util import filter_spans

# Precompile regex patterns
WHITESPACE_RE = re.compile(r"\s+")
NON_ALPHANUM_RE = re.compile(r"[^\w\s\-_]+")

# Initialize spaCy with minimal pipeline
spacy.prefer_gpu()
nlp = spacy.load(
    "en_core_web_sm",
    disable=["lemmatizer", "textcat", "vector"],  # Disable unused components
)

# Singleton PhraseMatcher for better performance


class KeywordMatcher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            cls._instance.batch_size = 1000
            cls._instance.patterns_cache = {}
        return cls._instance

    @lru_cache(maxsize=10000)
    def _create_pattern(self, text: str) -> Doc:
        return nlp.make_doc(text)

    def find_matches(self, doc: Doc, keywords: List[str]) -> Dict[str, List[int]]:
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


def extract_keywords(doc: Doc, top_n: int = 10, clean: bool = True) -> List[str]:
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
    chunk_spans = [chunk for chunk in doc.noun_chunks if not chunk.root.is_stop]
    all_spans = filter_spans(ent_spans + chunk_spans)

    # Process spans efficiently
    keywords = []
    seen_texts = set()

    for span in all_spans:
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
    keywords: List[str], keyword_positions: Dict[str, List[int]], n: int = 10
) -> List[Set[str]]:
    """Optimized proximity grouping using sorted positions."""
    # Early return for single or no keywords
    if len(keywords) <= 1:
        return [{kw} for kw in keywords]

    # Create flat list of positions for efficient processing
    positions: List[Tuple[int, str]] = [
        (pos, kw) for kw in keywords for pos in keyword_positions[kw]
    ]

    # Sort positions once
    positions.sort()

    # Initialize Union-Find with path compression and union by rank
    parent = {kw: kw for kw in keywords}
    rank = {kw: 0 for kw in keywords}

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


@lru_cache(maxsize=100)
def build_query_pattern(group_size: int, n: int) -> str:
    """Cache query patterns for common group sizes."""
    if group_size == 1:
        return '"{}"'
    return f"NEAR/{n}(" + " ".join('"{}"' for _ in range(group_size)) + ")"


def build_query(groups: List[Set[str]], n: int = 10) -> str:
    """Build query with cached patterns."""
    clauses = []

    for group in groups:
        if len(group) == 1:
            clauses.append(f'"{next(iter(group))}"')
        else:
            # Sort by length descending to prioritize longer phrases
            sorted_group = sorted(group, key=len, reverse=True)
            # Get cached pattern and format with keywords
            pattern = build_query_pattern(len(group), n)
            clause = pattern.format(*sorted_group)
            clauses.append(clause)

    return " OR ".join(clauses)


def paragraph_to_custom_queries(
    paragraph: str, top_n: int = 10, proximity_n: int = 10, min_keywords: int = 1
) -> List[str]:
    """
    Optimized paragraph processing with minimal behavior changes.
    Added min_keywords parameter to filter out low-value queries.
    """
    if not paragraph or not paragraph.strip():
        return []

    # Process entire paragraph once
    doc = nlp(paragraph)
    queries = []

    # Process sentences
    for sent in doc.sents:
        # Convert to doc for consistent API
        sent_doc = sent.as_doc()

        # Extract and clean keywords
        keywords = extract_keywords(sent_doc, top_n)
        if len(keywords) < min_keywords:
            continue

        # Find keyword positions using matcher
        keyword_positions = keyword_matcher.find_matches(sent_doc, keywords)

        # Skip if no keywords found in positions
        if not keyword_positions:
            continue

        # Find proximity groups and build query
        groups = find_proximity_groups(keywords, keyword_positions, proximity_n)
        query = build_query(groups, proximity_n)

        if query:
            queries.append(query)

    return queries
