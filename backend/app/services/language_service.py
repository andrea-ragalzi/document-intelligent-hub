# backend/app/services/language_service.py

from langdetect import detect
from translate import Translator

# TARGET LANGUAGE for RAG retrieval and indexing (forcing consistency)
RETRIEVAL_TARGET_LANGUAGE = "English"


class LanguageService:
    """
    Service dedicato per la gestione del rilevamento e della traduzione
    del linguaggio utilizzando librerie locali e gratuite (langdetect, translate).

    NOTA: Il linguaggio target per l'indicizzazione è sempre 'English'.
    """

    def __init__(self, target_lang: str = RETRIEVAL_TARGET_LANGUAGE):
        # Il linguaggio target è fisso su 'English' per la strategia RAG
        self.target_lang = target_lang

    def detect_language(self, content: str) -> str:
        """Rileva il codice lingua (due lettere, es. 'EN', 'IT') di un contenuto."""
        if not content or len(content.strip()) < 5:
            return "EN"  # Fallback per contenuti troppo corti

        try:
            # langdetect restituisce un codice a due lettere (es. 'en', 'it')
            lang_code = detect(content)
            return lang_code.upper()  # Restituisce il codice in maiuscolo

        except Exception as e:
            # langdetect genera un'eccezione per stringhe molto brevi/ambigue
            print(f"Error detecting language with langdetect: {e}. Falling back to EN.")
            return "EN"  # Fallback sicuro

    def translate_to_target(self, content: str) -> str:
        """Traduce il contenuto al linguaggio target (di default: English) per l'indicizzazione."""
        # NOTA: Questo metodo non è più usato in rag_service, ma mantenuto per la traduzione della risposta.
        try:
            # La libreria 'translate' utilizza l'endpoint pubblico di Google Translate
            translator = Translator(to_lang=self.target_lang)
            translation = translator.translate(content)
            return translation.strip()
        except (Exception, StopIteration) as e:
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
            return translation.strip()
        except (Exception, StopIteration) as e:
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
