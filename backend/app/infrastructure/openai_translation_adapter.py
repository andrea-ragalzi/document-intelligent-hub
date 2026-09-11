"""OpenAI adapter for retrieval and answer translation."""

from app.core.llm_configuration import chat_completion_options
from openai import OpenAI


class OpenAITranslationAdapter:
    """
    Service for translating user queries to document languages.

    This service ensures that queries are translated to match the language
    of the indexed documents, improving embedding similarity and retrieval quality.
    """

    # Language code to full name mapping
    LANGUAGE_NAMES: dict[str, str] = {
        "IT": "Italian",
        "EN": "English",
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

    def __init__(self, openai_client: OpenAI, model: str) -> None:
        """Initialize the adapter with its concrete client and model."""
        self.openai_client = openai_client
        self.model = model

    def translate_query_to_english(self, query: str) -> str:
        """
        Translate a query to English using OpenAI LLM.

        This method is used for legacy compatibility and when English
        is specifically required for certain operations.

        Args:
            query: The user query in any language

        Returns:
            The query translated to English, or original if already in English
        """
        prompt = (
            f"Translate the following user query to a standard, concise English search phrase. "
            f"If the query is already in English, return it unchanged. Query: '{query}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                **chat_completion_options(self.model, temperature=0.0),
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            return content.strip() if content else query

        except Exception as e:
            print(f"Error translating query to English: {e}. Using original query.")
            return query

    def translate_query_to_language(self, query: str, target_language: str) -> str:
        """
        Translate a query to the specified target language.

        This improves semantic matching when documents are in a specific language.
        Embeddings work better when query and documents are in the same language.
        Proper nouns (names, places, brands) are preserved in translation.

        Args:
            query: The original user query
            target_language: The target language code (e.g., 'IT', 'EN', 'FR')

        Returns:
            The query translated to the target language
        """
        target_lang_name = self.LANGUAGE_NAMES.get(target_language.upper(), "English")

        prompt = (
            f"Translate the following user query to {target_lang_name}. "
            f"Keep it concise and suitable for document search. "
            f"IMPORTANT: Do NOT translate proper nouns (person names, place names, company names, brands, product names). "
            f"Keep all proper nouns in their original form. "
            f"If the query is already in {target_lang_name}, return it unchanged. "
            f"Query: '{query}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                **chat_completion_options(self.model, temperature=0.0),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Preserve all proper nouns (names, places, brands) without translation.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            translated = content.strip() if content else query

            print(
                f"DEBUG [TranslationService]: Translated query to {target_language}: {translated}"
            )
            return translated

        except Exception as e:
            print(
                f"ERROR translating query to {target_language}: {e}. Using original query."
            )
            return query

    def translate_answer_back(self, answer: str, target_language: str) -> str:
        """
        Translate the generated answer back into the user's preferred language.

        Args:
            answer: Text in the answer generation language (usually English)
            target_language: The desired language code for the response

        Returns:
            The translated answer text.
        """
        prompt_language = self.LANGUAGE_NAMES.get(target_language.upper(), "English")
        prompt = (
            f"Translate the following assistant answer into {prompt_language}. "
            f"Preserve formatting and lists, but do not change proper nouns. Answer: '{answer}'"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert translator preserving tone and formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content
            translated = content.strip() if content else answer
            print(
                f"DEBUG [TranslationService]: Translated answer to {target_language}: {translated[:50]}..."
            )
            return translated
        except Exception as e:
            print(
                f"ERROR translating answer to {target_language}: {e}. Using original answer."
            )
            return answer

    def get_language_name(self, language_code: str) -> str:
        """
        Get the full language name from a language code.

        Args:
            language_code: ISO language code (e.g., 'IT', 'EN')

        Returns:
            Full language name (e.g., 'Italian', 'English')
        """
        return self.LANGUAGE_NAMES.get(language_code.upper(), "English")
