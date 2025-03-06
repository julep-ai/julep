# import numpy as np
# from ward import test

# from agents_api.autogen.openapi_model import DocReference, DocSnippet
# from agents_api.common.utils.mmr import apply_mmr_to_docs

# def create_test_doc(doc_id, embedding=None):
#     """Helper function to create test document references"""
#     return DocReference(
#         id=f"doc_{doc_id}",
#         snippet=DocSnippet(
#             content=f"Test content {doc_id}",
#             embedding=embedding,
#         ),
#         metadata={},
#     )


# @test("utility: test to apply_mmr_to_docs")
# def _():
#     # Create test documents with embeddings
#     docs = [
#         create_test_doc(1, np.array([0.1, 0.2, 0.3])),
#         create_test_doc(2, np.array([0.2, 0.3, 0.4])),
#         create_test_doc(3, np.array([0.3, 0.4, 0.5])),
#         create_test_doc(4, np.array([0.4, 0.5, 0.6])),
#         create_test_doc(5, np.array([0.5, 0.6, 0.7])),
#         create_test_doc(6, None),  # Doc without embedding
#     ]

#     query_embedding = np.array([0.3, 0.3, 0.3])

#     # Test with MMR strength = 0 (pure relevance)
#     result = apply_mmr_to_docs(docs, query_embedding, limit=3, mmr_strength=0)
#     assert len(result) == 3

#     # Test with MMR strength = 1 (maximum diversity)
#     result = apply_mmr_to_docs(docs, query_embedding, limit=3, mmr_strength=1)
#     assert len(result) == 3

#     # Test with not enough docs with embeddings
#     docs_few_embeddings = [
#         create_test_doc(1, np.array([0.1, 0.2, 0.3])),
#         create_test_doc(2, None),
#         create_test_doc(3, None),
#     ]

#     result = apply_mmr_to_docs(docs_few_embeddings, query_embedding, limit=2, mmr_strength=0.5)
#     assert len(result) == 3  # Should return original docs since not enough have embeddings

#     # Test with limit greater than available docs
#     result = apply_mmr_to_docs(docs, query_embedding, limit=10, mmr_strength=0.5)
#     assert len(result) == 5  # Only 5 docs have embeddings
