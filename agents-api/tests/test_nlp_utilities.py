import spacy
from agents_api.common.nlp import clean_keyword, extract_keywords, text_to_keywords
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


@test("utility: extract_keywords - split_chunks=False")
async def _():
    nlp = spacy.load("en_core_web_sm", exclude=["lemmatizer", "textcat"])
    doc = nlp("John Doe is a software engineer at Google.")
    assert set(extract_keywords(doc, split_chunks=False)) == {
        "John Doe",
        "a software engineer",
        "Google",
    }


@test("utility: extract_keywords - split_chunks=True")
async def _():
    nlp = spacy.load("en_core_web_sm", exclude=["lemmatizer", "textcat"])
    doc = nlp("John Doe is a software engineer at Google.")
    assert set(extract_keywords(doc, split_chunks=True)) == {
        "John Doe",
        "a",
        "software",
        "engineer",
        "Google",
    }


@test("utility: text_to_keywords - split_chunks=False")
async def _():
    test_cases = [
        # Single words
        ("test", {"test"}),
        # Multiple words in single sentence
        (
            "quick brown fox",
            {"quick brown fox"},  # Now kept as a single phrase due to proximity
        ),
        # Technical terms and phrases
        (
            "Machine Learning algorithm",
            {"Machine Learning algorithm"},  # Common technical phrase
        ),
        # Multiple sentences
        (
            "I love basketball especially Michael Jordan. LeBron James is also great.",
            {"basketball", "LeBron James", "Michael Jordan"},
        ),
        # Quoted phrases
        (
            '"quick brown fox"',
            {"quick brown fox"},  # Quotes removed, phrase kept together
        ),
        ('Find "machine learning" algorithms', {"machine learning"}),
        # Multiple quoted phrases
        ('"data science" and "machine learning"', {"machine learning", "data science"}),
        # Edge cases
        ("", set()),
        (
            "the and or",
            set(),  # All stop words should result in empty string
        ),
        (
            "a",
            set(),  # Single stop word should result in empty string
        ),
        ("X", set()),
        # Empty quotes
        ('""', set()),
        ('test "" phrase', {"phrase", "test"}),
        (
            "John Doe is a software engineer at Google.",
            {"Google", "John Doe", "a software engineer"},
        ),
        ("- Google", {"Google"}),
        # Test duplicate keyword handling
        (
            "John Doe is great. John Doe is awesome.",
            {"John Doe"},  # Should only include "John Doe" once
        ),
        (
            "Software Engineer at Google. Also, a Software Engineer.",
            {"Google", "Also a Software Engineer", "Software Engineer"},
        ),
    ]

    for input_text, expected_output in test_cases:
        print(f"Input: '{input_text}'")
        result = text_to_keywords(input_text, split_chunks=False)
        print(f"Generated query: '{result}'")
        print(f"Expected: '{expected_output}'\n")

        assert result == expected_output, (
            f"Expected terms {expected_output} but got {result} for input '{input_text}'"
        )


@test("utility: text_to_keywords - split_chunks=True")
async def _():
    test_cases = [
        # Single words
        ("test", {"test"}),
        # Multiple words in single sentence
        (
            "quick brown fox",
            {"quick", "brown", "fox"},  # Now kept as a single phrase due to proximity
        ),
        # Technical terms and phrases
        (
            "Machine Learning algorithm",
            {"Machine", "Learning", "algorithm"},  # Common technical phrase
        ),
        # Multiple sentences
        (
            "I love basketball especially Michael Jordan. LeBron James is also great.",
            {"basketball", "LeBron James", "Michael Jordan"},
        ),
        # Quoted phrases
        (
            '"quick brown fox"',
            {"quick", "brown", "fox"},  # Quotes removed, phrase kept together
        ),
        ('Find "machine learning" algorithms', {"machine", "learning"}),
        # Multiple quoted phrases
        ('"data science" and "machine learning"', {"machine", "learning", "data", "science"}),
        # Edge cases
        ("", set()),
        (
            "the and or",
            set(),  # All stop words should result in empty string
        ),
        (
            "a",
            set(),  # Single stop word should result in empty string
        ),
        ("X", set()),
        # Empty quotes
        ('""', set()),
        ('test "" phrase', {"phrase", "test"}),
        (
            "John Doe is a software engineer at Google.",
            {"Google", "John Doe", "software", "engineer"},
        ),
        # Test duplicate keyword handling
        (
            "John Doe is great. John Doe is awesome.",
            {"John Doe"},  # Should only include "John Doe" once even with split_chunks=True
        ),
        (
            "Software Engineer at Google. Also, a Software Engineer.",
            {"Also", "Google", "Software", "Engineer"},  # When split, each word appears once
        ),
    ]

    for input_text, expected_output in test_cases:
        print(f"Input: '{input_text}'")
        result = text_to_keywords(input_text, split_chunks=True)
        print(f"Generated query: '{result}'")
        print(f"Expected: '{expected_output}'\n")

        assert result == expected_output, (
            f"Expected terms {expected_output} but got {result} for input '{input_text}'"
        )
