# =========================================================
# retrieval/embedding.py
# =========================================================

import logging
import numpy as np
import torch

from typing import List, Union

from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL_NAME,
    USE_GPU,
    BATCH_SIZE,
    EMBEDDING_DIM
)


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# BIOMEDICAL EMBEDDING ENGINE
# =========================================================

class BioBERTEmbedding:

    # =====================================================
    # SHARED MODEL INSTANCE
    # =====================================================

    _model = None

    _device = "cpu"

    _initialized = False

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        try:

            # =================================================
            # LOAD MODEL ONLY ONCE
            # =================================================

            if not BioBERTEmbedding._initialized:

                logger.info(
                    "Loading BioBERT embedding model..."
                )

                if USE_GPU and torch.cuda.is_available():

                    BioBERTEmbedding._device = "cuda"

                else:

                    BioBERTEmbedding._device = "cpu"

                logger.info(
                    f"Using device: {BioBERTEmbedding._device}"
                )

                BioBERTEmbedding._model = SentenceTransformer(

                    EMBEDDING_MODEL_NAME,

                    device=BioBERTEmbedding._device
                )

                BioBERTEmbedding._initialized = True

                logger.info(
                    "BioBERT model loaded successfully"
                )

            self.model = BioBERTEmbedding._model

            # =================================================
            # EMBEDDING DIMENSION
            # =================================================

            self.embedding_dimension = (

                self.model.get_sentence_embedding_dimension()
            )

            logger.info(
                f"Embedding Dimension: "
                f"{self.embedding_dimension}"
            )

        except Exception as error:

            logger.error(
                f"Error loading embedding model: {error}"
            )

            raise RuntimeError(

                f"Failed to initialize "
                f"embedding model: {error}"
            )

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    def _clean_text(

        self,

        text: Union[str, None]

    ) -> str:

        if text is None:

            return ""

        text = str(text).strip()

        if text.lower() in [

            "none",
            "null",
            "nan"
        ]:

            return ""

        return text

    # =====================================================
    # SAFE ZERO VECTOR
    # =====================================================

    def _zero_vector(self) -> np.ndarray:

        return np.zeros(

            EMBEDDING_DIM,

            dtype=np.float32
        )

    # =====================================================
    # SINGLE TEXT EMBEDDING
    # =====================================================

    def encode(

        self,

        text: str

    ) -> np.ndarray:

        try:

            cleaned_text = self._clean_text(text)

            # =============================================
            # EMPTY TEXT PROTECTION
            # =============================================

            if cleaned_text == "":

                return self._zero_vector()

            with torch.no_grad():

                embedding = self.model.encode(

                    cleaned_text,

                    convert_to_numpy=True,

                    normalize_embeddings=True,

                    show_progress_bar=False
                )

            embedding = embedding.astype(np.float32)

            # =============================================
            # SAFE DIMENSION CHECK
            # =============================================

            if embedding.shape[0] != EMBEDDING_DIM:

                logger.warning(
                    "Embedding dimension mismatch detected"
                )

            return embedding

        except Exception as error:

            logger.error(
                f"Encoding failed: {error}"
            )

            return self._zero_vector()

    # =====================================================
    # ALIAS METHOD
    # =====================================================

    def generate_embedding(

        self,

        text: str

    ) -> np.ndarray:

        return self.encode(text)

    # =====================================================
    # MULTIPLE TEXT EMBEDDINGS
    # =====================================================

    def encode_batch(

        self,

        texts: List[str]

    ) -> np.ndarray:

        try:

            if not isinstance(texts, list):

                texts = []

            cleaned_texts = [

                self._clean_text(text)

                for text in texts
            ]

            if len(cleaned_texts) == 0:

                return np.zeros(

                    (0, EMBEDDING_DIM),

                    dtype=np.float32
                )

            with torch.no_grad():

                embeddings = self.model.encode(

                    cleaned_texts,

                    batch_size=BATCH_SIZE,

                    convert_to_numpy=True,

                    normalize_embeddings=True,

                    show_progress_bar=False
                )

            embeddings = embeddings.astype(np.float32)

            return embeddings

        except Exception as error:

            logger.error(
                f"Batch encoding failed: {error}"
            )

            return np.zeros(

                (
                    len(texts),
                    EMBEDDING_DIM
                ),

                dtype=np.float32
            )

    # =====================================================
    # COSINE SIMILARITY
    # =====================================================

    def cosine_similarity(

        self,

        embedding_1: np.ndarray,

        embedding_2: np.ndarray

    ) -> float:

        try:

            if embedding_1 is None or embedding_2 is None:

                return 0.0

            norm_1 = np.linalg.norm(
                embedding_1
            )

            norm_2 = np.linalg.norm(
                embedding_2
            )

            # =============================================
            # PREVENT DIVISION BY ZERO
            # =============================================

            if norm_1 == 0 or norm_2 == 0:

                return 0.0

            similarity = np.dot(

                embedding_1,
                embedding_2

            ) / (

                norm_1 * norm_2
            )

            similarity = float(similarity)

            # =============================================
            # SAFE CLAMPING
            # =============================================

            similarity = max(
                -1.0,
                min(1.0, similarity)
            )

            return similarity

        except Exception as error:

            logger.error(
                f"Similarity computation failed: {error}"
            )

            return 0.0

    # =====================================================
    # VECTOR DIMENSION
    # =====================================================

    def get_embedding_dimension(self) -> int:

        return self.embedding_dimension


# =========================================================
# GLOBAL SHARED INSTANCE
# =========================================================

embedding_model = BioBERTEmbedding()


# =========================================================
# TEST BLOCK
# =========================================================

if __name__ == "__main__":

    try:

        sample_text = (

            "Patient has severe lower back pain "
            "with difficulty walking."
        )

        embedding = embedding_model.encode(
            sample_text
        )

        print(
            "Embedding Shape:",
            embedding.shape
        )

        print(
            "Embedding Dimension:",
            embedding_model.get_embedding_dimension()
        )

        print(
            "Embedding Sample:",
            embedding[:10]
        )

        similarity = embedding_model.cosine_similarity(

            embedding,
            embedding
        )

        print(
            "Self Similarity:",
            similarity
        )

    except Exception as error:

        print(
            f"Test failed: {error}"
        )