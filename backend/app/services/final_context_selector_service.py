"""Bounded, score-preserving final context selection."""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.documents import Document


class FinalContextSelector:
    """Select complementary evidence from already reranked candidates.

    This service does not calculate or modify reranker scores. It only applies a
    bounded relative-score gate and deterministic diversity tie-breaking.
    """

    relative_threshold = 0.70
    min_final_chunks = 2
    max_final_chunks = 5
    # Treat close scores as ties for bounded diversity selection.  A slightly
    # wider margin keeps complementary, provenance-bearing evidence from being
    # crowded out by several near-identical fragments from one page.
    _similar_score_margin = 0.10

    def select(self, candidates: Sequence[Document]) -> list[Document]:
        """Return up to five provenance-preserving context documents."""
        ranked = self._stable_rank(candidates)
        if len(ranked) <= self.min_final_chunks:
            return ranked

        best_score = self._score(ranked[0])
        threshold_eligible = [
            document
            for document in ranked
            if self._score(document) >= best_score * self.relative_threshold
        ]
        selected = self._choose_complementary(threshold_eligible)

        if len(selected) < self.min_final_chunks:
            selected = self._fill_minimum(selected, ranked)
        return selected[: self.max_final_chunks]

    def _choose_complementary(self, candidates: Sequence[Document]) -> list[Document]:
        remaining = list(candidates)
        selected: list[Document] = []
        while remaining and len(selected) < self.max_final_chunks:
            candidate = self._choose_next(remaining, selected)
            remaining.remove(candidate)
            if self._redundant(candidate, selected):
                continue
            selected.append(candidate)
        return selected

    def _fill_minimum(
        self, selected: list[Document], ranked: Sequence[Document]
    ) -> list[Document]:
        result = list(selected)
        for candidate in ranked:
            if candidate in result:
                continue
            if not self._redundant(candidate, result):
                result.append(candidate)
            if len(result) >= self.min_final_chunks:
                return result
        # The bound is more important than avoiding the only available duplicate.
        for candidate in ranked:
            if candidate not in result:
                result.append(candidate)
            if len(result) >= self.min_final_chunks:
                break
        return result

    def _choose_next(
        self, remaining: Sequence[Document], selected: Sequence[Document]
    ) -> Document:
        strongest = remaining[0]
        comparable = [
            candidate
            for candidate in remaining
            if self._score(strongest) - self._score(candidate)
            <= self._similar_score_margin
        ]
        selected_files = {self._filename(document) for document in selected}
        selected_pages = {self._page_key(document) for document in selected}
        new_file = next(
            (candidate for candidate in comparable if self._filename(candidate) not in selected_files),
            None,
        )
        if new_file is not None:
            return new_file
        new_page = next(
            (candidate for candidate in comparable if self._page_key(candidate) not in selected_pages),
            None,
        )
        return new_page or strongest

    @classmethod
    def _stable_rank(cls, candidates: Sequence[Document]) -> list[Document]:
        return [
            candidate
            for _, candidate in sorted(
                enumerate(candidates), key=lambda item: (-cls._score(item[1]), item[0])
            )
        ]

    @staticmethod
    def _score(document: Document) -> float:
        value = document.metadata.get("rerank_score", 0.0)
        return float(value) if isinstance(value, int | float) else 0.0

    @staticmethod
    def _filename(document: Document) -> str:
        return str(document.metadata.get("original_filename", ""))

    @classmethod
    def _page_key(cls, document: Document) -> tuple[str, str]:
        return cls._filename(document), str(document.metadata.get("page_number", ""))

    @classmethod
    def _redundant(cls, candidate: Document, selected: Sequence[Document]) -> bool:
        candidate_text = cls._normalized_text(candidate)
        candidate_words = set(candidate_text.split())
        for existing in selected:
            existing_text = cls._normalized_text(existing)
            if candidate_text == existing_text:
                return True
            if cls._page_key(candidate) != cls._page_key(existing):
                continue
            existing_words = set(existing_text.split())
            union = candidate_words | existing_words
            if union and len(candidate_words & existing_words) / len(union) >= 0.90:
                return True
        return False

    @staticmethod
    def _normalized_text(document: Document) -> str:
        return " ".join(document.page_content.casefold().split())


final_context_selector = FinalContextSelector()
