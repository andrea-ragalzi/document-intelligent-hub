"""
Centralized language configuration for the application.

This module defines all supported languages with their metadata, including:
- Language code (ISO 639-1)
- English name
- Native name
- Flag emoji
- "Sources" label translation

This serves as the single source of truth for language support across the application.
"""

from typing import TypedDict


class LanguageMetadata(TypedDict):
    """Type definition for language metadata."""
    code: str
    english_name: str
    native_name: str
    flag: str
    sources_label: str


SUPPORTED_LANGUAGES: list[LanguageMetadata] = [
    {
        "code": "EN",
        "english_name": "English",
        "native_name": "English",
        "flag": "🇬🇧",
        "sources_label": "Sources"
    },
    {
        "code": "IT",
        "english_name": "Italian",
        "native_name": "Italiano",
        "flag": "🇮🇹",
        "sources_label": "Fonti"
    },
    {
        "code": "ES",
        "english_name": "Spanish",
        "native_name": "Español",
        "flag": "🇪🇸",
        "sources_label": "Fuentes"
    },
    {
        "code": "FR",
        "english_name": "French",
        "native_name": "Français",
        "flag": "🇫🇷",
        "sources_label": "Sources"
    },
    {
        "code": "DE",
        "english_name": "German",
        "native_name": "Deutsch",
        "flag": "🇩🇪",
        "sources_label": "Quellen"
    },
    {
        "code": "PT",
        "english_name": "Portuguese",
        "native_name": "Português",
        "flag": "🇵🇹",
        "sources_label": "Fontes"
    },
    {
        "code": "NL",
        "english_name": "Dutch",
        "native_name": "Nederlands",
        "flag": "🇳🇱",
        "sources_label": "Bronnen"
    },
    {
        "code": "PL",
        "english_name": "Polish",
        "native_name": "Polski",
        "flag": "🇵🇱",
        "sources_label": "Źródła"
    },
    {
        "code": "RU",
        "english_name": "Russian",
        "native_name": "Русский",
        "flag": "🇷🇺",
        "sources_label": "Источники"
    },
    {
        "code": "ZH",
        "english_name": "Chinese",
        "native_name": "中文",
        "flag": "🇨🇳",
        "sources_label": "来源"
    },
    {
        "code": "JA",
        "english_name": "Japanese",
        "native_name": "日本語",
        "flag": "🇯🇵",
        "sources_label": "出典"
    },
    {
        "code": "KO",
        "english_name": "Korean",
        "native_name": "한국어",
        "flag": "🇰🇷",
        "sources_label": "출처"
    },
    {
        "code": "AR",
        "english_name": "Arabic",
        "native_name": "العربية",
        "flag": "🇸🇦",
        "sources_label": "المصادر"
    },
    {
        "code": "TR",
        "english_name": "Turkish",
        "native_name": "Türkçe",
        "flag": "🇹🇷",
        "sources_label": "Kaynaklar"
    },
    {
        "code": "SV",
        "english_name": "Swedish",
        "native_name": "Svenska",
        "flag": "🇸🇪",
        "sources_label": "Källor"
    },
    {
        "code": "NO",
        "english_name": "Norwegian",
        "native_name": "Norsk",
        "flag": "🇳🇴",
        "sources_label": "Kilder"
    },
    {
        "code": "DA",
        "english_name": "Danish",
        "native_name": "Dansk",
        "flag": "🇩🇰",
        "sources_label": "Kilder"
    },
    {
        "code": "FI",
        "english_name": "Finnish",
        "native_name": "Suomi",
        "flag": "🇫🇮",
        "sources_label": "Lähteet"
    },
    {
        "code": "EL",
        "english_name": "Greek",
        "native_name": "Ελληνικά",
        "flag": "🇬🇷",
        "sources_label": "Πηγές"
    },
    {
        "code": "CS",
        "english_name": "Czech",
        "native_name": "Čeština",
        "flag": "🇨🇿",
        "sources_label": "Zdroje"
    }
]


def get_sources_label(language_code: str) -> str:
    """
    Get the translated "Sources" label for a given language code.
    
    Args:
        language_code: ISO 639-1 language code (e.g., "EN", "IT", "ES")
    
    Returns:
        Translated "Sources" label for the language, defaults to "Sources" if not found
    """
    language_code_upper = language_code.upper()
    for lang in SUPPORTED_LANGUAGES:
        if lang["code"] == language_code_upper:
            return lang["sources_label"]
    return "Sources"  # Fallback to English


def get_language_codes() -> list[str]:
    """
    Get list of all supported language codes.
    
    Returns:
        List of language codes (e.g., ["EN", "IT", "ES", ...])
    """
    return [lang["code"] for lang in SUPPORTED_LANGUAGES]
