import re
from collections import Counter, defaultdict

import spacy

# Load spaCy English model
spacy.prefer_gpu()
nlp = spacy.load("en_core_web_sm")


def extract_keywords(text: str, top_n: int = 10, clean: bool = True) -> list[str]:
    """
    Extracts significant keywords and phrases from the text.

    Args:
        text (str): The input text to process.
        top_n (int): Number of top keywords to extract based on frequency.
        clean (bool): Strip non-alphanumeric characters from keywords.

    Returns:
        List[str]: A list of extracted keywords/phrases.
    """
    doc = nlp(text)

    # Extract named entities
    entities = [
        ent.text.strip()
        for ent in doc.ents
        if ent.label_
        not in ["DATE", "TIME", "PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL"]
    ]

    # Extract nouns and proper nouns
    nouns = [
        chunk.text.strip().lower()
        for chunk in doc.noun_chunks
        if not chunk.root.is_stop
    ]

    # Combine entities and nouns
    combined = entities + nouns

    # Normalize and count frequency
    normalized = [re.sub(r"\s+", " ", kw).strip() for kw in combined]
    freq = Counter(normalized)

    # Get top_n keywords
    keywords = [item for item, count in freq.most_common(top_n)]

    if clean:
        keywords = [re.sub(r"[^\w\s\-_]+", "", kw) for kw in keywords]

    return keywords


def find_keyword_positions(doc, keyword: str) -> list[int]:
    """
    Finds all start indices of the keyword in the tokenized doc.

    Args:
        doc (spacy.tokens.Doc): The tokenized document.
        keyword (str): The keyword or phrase to search for.

    Returns:
        List[int]: List of starting token indices where the keyword appears.
    """
    keyword_tokens = keyword.split()
    n = len(keyword_tokens)
    positions = []
    for i in range(len(doc) - n + 1):
        window = doc[i : i + n]
        window_text = " ".join([token.text.lower() for token in window])
        if window_text == keyword:
            positions.append(i)
    return positions


def find_proximity_groups(
    text: str, keywords: list[str], n: int = 10
) -> list[set[str]]:
    """
    Groups keywords that appear within n words of each other.

    Args:
        text (str): The input text.
        keywords (List[str]): List of keywords to consider.
        n (int): The proximity window in words.

    Returns:
        List[Set[str]]: List of sets, each containing keywords that are proximate.
    """
    doc = nlp(text.lower())
    keyword_positions = defaultdict(list)

    for kw in keywords:
        positions = find_keyword_positions(doc, kw)
        keyword_positions[kw].extend(positions)

    # Initialize Union-Find structure
    parent = {}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    def union(u, v):
        u_root = find(u)
        v_root = find(v)
        if u_root == v_root:
            return
        parent[v_root] = u_root

    # Initialize each keyword as its own parent
    for kw in keywords:
        parent[kw] = kw

    # Compare all pairs of keywords
    for i in range(len(keywords)):
        for j in range(i + 1, len(keywords)):
            kw1 = keywords[i]
            kw2 = keywords[j]
            positions1 = keyword_positions[kw1]
            positions2 = keyword_positions[kw2]
            # Check if any positions are within n words
            for pos1 in positions1:
                for pos2 in positions2:
                    distance = abs(pos1 - pos2)
                    if distance <= n:
                        union(kw1, kw2)
                        break
                else:
                    continue
                break

    # Group keywords by their root parent
    groups = defaultdict(set)
    for kw in keywords:
        root = find(kw)
        groups[root].add(kw)

    # Convert to list of sets
    group_list = list(groups.values())

    return group_list


def build_query(groups: list[set[str]], keywords: list[str], n: int = 10) -> str:
    """
    Builds a query string using the custom query language.

    Args:
        groups (List[Set[str]]): List of keyword groups.
        keywords (List[str]): Original list of keywords.
        n (int): The proximity window for NEAR.

    Returns:
        str: The constructed query string.
    """
    grouped_keywords = set()
    clauses = []

    for group in groups:
        if len(group) == 1:
            clauses.append(f'"{list(group)[0]}"')
        else:
            sorted_group = sorted(
                group, key=lambda x: -len(x)
            )  # Sort by length to prioritize phrases
            escaped_keywords = [f'"{kw}"' for kw in sorted_group]
            near_clause = f"NEAR/{n}(" + " ".join(escaped_keywords) + ")"
            clauses.append(near_clause)
        grouped_keywords.update(group)

    # Identify keywords not in any group (if any)
    remaining = set(keywords) - grouped_keywords
    for kw in remaining:
        clauses.append(f'"{kw}"')

    # Combine all clauses with OR
    query = " OR ".join(clauses)

    return query


def text_to_custom_query(text: str, top_n: int = 10, proximity_n: int = 10) -> str:
    """
    Converts arbitrary text to the custom query language.

    Args:
        text (str): The input text to convert.
        top_n (int): Number of top keywords to extract.
        proximity_n (int): The proximity window for NEAR/n.

    Returns:
        str: The custom query string.
    """
    keywords = extract_keywords(text, top_n)
    if not keywords:
        return ""
    groups = find_proximity_groups(text, keywords, proximity_n)
    query = build_query(groups, keywords, proximity_n)
    return query


def paragraph_to_custom_queries(paragraph: str) -> list[str]:
    """
    Converts a paragraph to a list of custom query strings.

    Args:
        paragraph (str): The input paragraph to convert.

    Returns:
        List[str]: The list of custom query strings.
    """

    queries = [text_to_custom_query(sentence.text) for sentence in nlp(paragraph).sents]
    queries = [q for q in queries if q]

    return queries
