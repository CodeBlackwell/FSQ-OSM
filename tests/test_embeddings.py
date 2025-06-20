from sentence_transformers import SentenceTransformer
import numpy as np

def test_embedding_generation():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    names = ["Starbucks", "Joe's Pizza", "Central Park"]
    embeddings = model.encode(names)
    assert embeddings.shape == (3, 384)
    # Check that embeddings for different names are not identical
    assert not np.allclose(embeddings[0], embeddings[1])
    assert not np.allclose(embeddings[1], embeddings[2])
    # Check that embedding is a numpy array of correct dtype
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.dtype == np.float32 or embeddings.dtype == np.float64
