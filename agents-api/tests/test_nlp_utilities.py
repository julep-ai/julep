import spacy
from agents_api.common.nlp import clean_keyword, extract_keywords, text_to_tsvector_query
from ward import test


@test("utility: clean_keyword")
async def _():
    assert clean_keyword("Hello, World!") == "Hello World"

    # Basic cleaning
    # assert clean_keyword("test@example.com") == "test example com"
    assert clean_keyword("user-name_123") == "user-name_123"
    assert clean_keyword("  spaces  ") == "spaces"

    # Special characters
    assert clean_keyword("$price: 100%") == "price 100"
    assert clean_keyword("#hashtag!") == "hashtag"

    # Multiple spaces and punctuation
    assert clean_keyword("multiple,   spaces...") == "multiple spaces"

    # Empty and whitespace
    assert clean_keyword("") == ""
    assert clean_keyword("   ") == ""

    assert clean_keyword("- try") == "try"


@test("utility: extract_keywords")
async def _():
    nlp = spacy.load("en_core_web_sm", exclude=["lemmatizer", "textcat"])
    doc = nlp("John Doe is a software engineer at Google.")
    assert set(extract_keywords(doc)) == {"John Doe", "a software engineer", "Google"}


@test("utility: text_to_tsvector_query - split_chunks=False")
async def _():
    test_cases = [
        # Single words
        ("test", "test"),
        # Multiple words in single sentence
        (
            "quick brown fox",
            "quick brown fox",  # Now kept as a single phrase due to proximity
        ),
        # Technical terms and phrases
        (
            "Machine Learning algorithm",
            "machine learning algorithm",  # Common technical phrase
        ),
        # Multiple sentences
        (
            "I love basketball especially Michael Jordan. LeBron James is also great.",
            "basketball OR lebron james OR michael jordan",
        ),
        # Quoted phrases
        (
            '"quick brown fox"',
            "quick brown fox",  # Quotes removed, phrase kept together
        ),
        ('Find "machine learning" algorithms', "machine learning"),
        # Multiple quoted phrases
        ('"data science" and "machine learning"', "machine learning OR data science"),
        # Edge cases
        ("", ""),
        (
            "the and or",
            "",  # All stop words should result in empty string
        ),
        (
            "a",
            "",  # Single stop word should result in empty string
        ),
        ("X", "X"),
        # Empty quotes
        ('""', ""),
        ('test "" phrase', "phrase OR test"),
        (
            "John Doe is a software engineer at Google.",
            "google OR john doe OR a software engineer",
        ),
        ("- google", "google"),
    ]

    for input_text, expected_output in test_cases:
        print(f"Input: '{input_text}'")
        result = text_to_tsvector_query(input_text, split_chunks=False)
        print(f"Generated query: '{result}'")
        print(f"Expected: '{expected_output}'\n")

        result_terms = {term.lower() for term in result.split(" OR ") if term}
        expected_terms = {term.lower() for term in expected_output.split(" OR ") if term}
        assert result_terms == expected_terms, (
            f"Expected terms {expected_terms} but got {result_terms} for input '{input_text}'"
        )


@test("utility: text_to_tsvector_query - split_chunks=True")
async def _():
    test_cases = [
        # Single words
        ("test", "test"),
        # Multiple words in single sentence
        (
            "quick brown fox",
            "quick OR brown OR fox",  # Now kept as a single phrase due to proximity
        ),
        # Technical terms and phrases
        (
            "Machine Learning algorithm",
            "machine OR learning OR algorithm",  # Common technical phrase
        ),
        # Multiple sentences
        (
            "I love basketball especially Michael Jordan. LeBron James is also great.",
            "basketball OR lebron james OR michael jordan",
        ),
        # Quoted phrases
        (
            '"quick brown fox"',
            "quick OR brown OR fox",  # Quotes removed, phrase kept together
        ),
        ('Find "machine learning" algorithms', "machine OR learning"),
        # Multiple quoted phrases
        ('"data science" and "machine learning"', "machine OR learning OR data OR science"),
        # Edge cases
        ("", ""),
        (
            "the and or",
            "",  # All stop words should result in empty string
        ),
        (
            "a",
            "",  # Single stop word should result in empty string
        ),
        ("X", "X"),
        # Empty quotes
        ('""', ""),
        ('test "" phrase', "phrase OR test"),
        (
            "John Doe is a software engineer at Google.",
            "google OR john doe OR a OR software OR engineer",
        ),
    ]

    for input_text, expected_output in test_cases:
        print(f"Input: '{input_text}'")
        result = text_to_tsvector_query(input_text, split_chunks=True)
        print(f"Generated query: '{result}'")
        print(f"Expected: '{expected_output}'\n")

        result_terms = {term.lower() for term in result.split(" OR ") if term}
        expected_terms = {term.lower() for term in expected_output.split(" OR ") if term}
        assert result_terms == expected_terms, (
            f"Expected terms {expected_terms} but got {result_terms} for input '{input_text}'"
        )
