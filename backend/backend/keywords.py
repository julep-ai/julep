from keybert import KeyBERT
from keyphrase_vectorizers import KeyphraseCountVectorizer

vectorizer = KeyphraseCountVectorizer(pos_pattern="<N.*>")
kw_model = KeyBERT(model="all-MiniLM-L6-v2")


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


if __name__ == "__main__":
    extract_keywords(
        "Diwank's mom's name is Shikha Singh. She is an entrepreneur and a very inspiring and brave person."
    )
