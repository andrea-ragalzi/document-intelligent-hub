# backend/app/services/language_service.py

import re
import unicodedata
from collections.abc import Iterable

from lingua import LanguageDetectorBuilder  # pylint: disable=no-name-in-module
from translate import Translator

from app.core.constants import LanguageConstants

# English is a retrieval-translation target, never a final-answer language rule.
RETRIEVAL_TARGET_LANGUAGE = "English"


class LanguageService:
    """
    Service dedicato per la gestione del rilevamento e della traduzione
    del linguaggio utilizzando librerie locali e gratuite (Lingua, translate).

    English is used only when a retrieval query needs translation.
    """

    def __init__(self, target_lang: str = RETRIEVAL_TARGET_LANGUAGE) -> None:
        # Retrieval translation stays independent from final answer generation.
        self.target_lang = target_lang
        self._detector = LanguageDetectorBuilder.from_all_languages().build()

    def detect_language(
        self, content: str, fallback_language: str | None = "en"
    ) -> str:
        """Detect a reliable ISO 639-1 code, falling back when confidence is low."""
        return self.detect_language_reliably(content) or fallback_language or "en"

    def resolve_response_language(
        self,
        content: str,
        fallback_language: str | None = "en",
        *,
        output_language: str | None = None,
        recent_user_messages: Iterable[str] | None = None,
    ) -> str:
        """Resolve the response language from the current turn before the answer LLM."""
        if output_language:
            return output_language.lower()
        explicit_language = self._explicit_response_language(content)
        if explicit_language:
            return explicit_language

        detected_language = self.detect_language_reliably(content)
        if detected_language:
            return detected_language

        if recent_user_messages:
            for recent_message in recent_user_messages:
                recent_language = self.detect_language_reliably(recent_message)
                if recent_language:
                    return recent_language
        return fallback_language or "en"

    def detect_language_reliably(  # pylint: disable=too-many-return-statements
        self, content: str
    ) -> str | None:
        """Return a detected code only when Lingua has sufficient confidence."""
        if not content or len(content.strip()) < 5:
            return None

        try:
            lexical_language = self._language_from_lexical_evidence(content)
            if lexical_language:
                return lexical_language

            confidence_values = list(
                self._detector.compute_language_confidence_values(content)
            )
            confidence_values.sort(key=lambda value: value.value, reverse=True)
            if not confidence_values:
                return None

            top = confidence_values[0]
            second_value = confidence_values[1].value if len(confidence_values) > 1 else 0.0
            # Calibrated from the observed short-query cases: stable examples
            # have top >= .098 and a margin >= .025; "Chi e Alice?" has .078
            # and .010, so its top result is intentionally treated as ambiguous.
            if top.value < 0.09 or top.value - second_value < 0.02:
                return self._language_from_lexical_evidence(content)

            language_code = top.language.iso_code_639_1.name.lower()
            if language_code.upper() not in LanguageConstants.SUPPORTED_LANGUAGES:
                return self._language_from_lexical_evidence(content)
            return language_code

        except Exception as e:
            print(f"Error detecting language with Lingua: {e}. Falling back to EN.")
            return None

    @staticmethod
    def _normalize_text(content: str) -> str:
        return "".join(
            char
            for char in unicodedata.normalize("NFD", content.lower())
            if unicodedata.category(char) != "Mn"
        )

    def _explicit_response_language(self, content: str) -> str | None:
        normalized = self._normalize_text(content)
        language_names = {
            "italiano": "it",
            "italian": "it",
            "inglese": "en",
            "english": "en",
            "spagnolo": "es",
            "espanol": "es",
            "spanish": "es",
            "francese": "fr",
            "francais": "fr",
            "french": "fr",
            "tedesco": "de",
            "deutsch": "de",
            "german": "de",
        }
        request_markers = (
            "answer",
            "respond",
            "reply",
            "rispondi",
            "rispondere",
            "responde",
            "responder",
            "reponds",
            "antworte",
            "antworten",
        )
        for name, code in language_names.items():
            if re.search(rf"\b{name}\b", normalized) and any(
                marker in normalized for marker in request_markers
            ):
                return code
        return None

    def _language_from_lexical_evidence(self, content: str) -> str | None:
        """Recognize common short question forms before all-language Lingua scoring."""
        normalized = self._normalize_text(content)
        patterns = {
            "en": (r"\bwho\s+(?:is|was|are)\b", r"\band\s+him\b"),
            "it": (
                r"\bchi\s+(?:e|è)\b",
                r"\bperche\b",
                r"\bcosa\s+succede\b",
            ),
            "es": (
                r"\bquien\s+(?:es|eres)\b",
                r"\besta\s+(?:muerto|muerta)\b",
                r"\by\s+el\b",
            ),
            "fr": (r"\bqui\s+est\b",),
            "de": (r"\bwer\s+ist\b",),
        }
        for language_code, language_patterns in patterns.items():
            if any(re.search(pattern, normalized) for pattern in language_patterns):
                return language_code
        return None

    def translate_to_target(self, content: str) -> str:
        """Traduce il contenuto al linguaggio target (di default: English) per l'indicizzazione."""
        # NOTA: Questo metodo non è più usato in rag_service, ma mantenuto per la traduzione della risposta.
        try:
            # La libreria 'translate' utilizza l'endpoint pubblico di Google Translate
            translator = Translator(to_lang=self.target_lang)
            translation = translator.translate(content)
            return str(translation).strip()
        except Exception as e:
            # Cattura StopIteration, errore comune per il fallimento della traduzione
            print(
                f"Translation failed (Type: {type(e).__name__}). Returning original content."
            )
            return content  # Restituisce il contenuto originale come fallback

    def translate_answer_back(self, answer: str, target_language_code: str) -> str:
        """Traduce la risposta RAG (che è in target_lang) alla lingua originale dell'utente."""

        # Evita la traduzione se la lingua target è già inglese (o EN)
        if (
            target_language_code.upper() == self.target_lang.upper()
            or target_language_code.upper() == "EN"
        ):
            return answer

        try:
            # Assumiamo che target_language_code sia un codice a due lettere (es. 'IT')
            translator = Translator(to_lang=target_language_code.lower())
            translation = translator.translate(answer)
            return str(translation).strip()
        except Exception as e:
            print(
                f"Translation failed (Type: {type(e).__name__}). Returning English answer."
            )
            return answer  # Restituisce la risposta inglese originale come fallback

    def get_language_name(self, language_code: str) -> str:
        """
        Get the full language name from a language code.

        Args:
            language_code: ISO language code (e.g., 'IT', 'EN')

        Returns:
            Full language name (e.g., 'Italian', 'English')
        """
        language_names = {
            "EN": "English",
            "IT": "Italian",
            "FR": "French",
            "DE": "German",
            "ES": "Spanish",
            "PT": "Portuguese",
            "NL": "Dutch",
            "PL": "Polish",
            "RU": "Russian",
            "ZH": "Chinese",
            "JA": "Japanese",
            "KO": "Korean",
        }
        return language_names.get(language_code.upper(), "Unknown")


language_service = LanguageService()
