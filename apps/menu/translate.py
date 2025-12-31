"""
Module apps.kitchen.translate

Provides translation utilities using Azure Translator with local caching.

Features:
- translate(): Translate a single string.
- translate_many(): Batch translate multiple strings.
- Automatic caching in memory and on disk to reduce API calls.
- Helper functions for language management and endpoint handling.

Constants:
- LANGUAGES: List of supported language codes.
- TRANSLATION_CACHE: In-memory cache for translations.
- CACHE_FILE: File path for persistent cache.

"""

import requests
import uuid
import random
import json
import os
from django.conf import settings

AZURE_KEY = settings.AZURE_TRANSLATOR["KEY"]
AZURE_REGION = settings.AZURE_TRANSLATOR["REGION"]
AZURE_ENDPOINT = settings.AZURE_TRANSLATOR["ENDPOINT"]

LANGUAGES = ["en", "es", "fr", "de", "ja", "ko", "zh-Hans", "ar", "it"]

# Cache file path
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'translation_cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'translations.json')

# Global in-memory cache: { (text, lang) : translated_text }
TRANSLATION_CACHE = {}


def _ensure_cache_dir():
    """Ensure the translation cache directory exists on disk."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)


def _load_cache_from_file():
    """Load translations from JSON file into memory cache."""
    global TRANSLATION_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert list of [text, lang, translated] back to tuple keys
                TRANSLATION_CACHE = {
                    (item[0], item[1]): item[2] for item in data.get('translations', [])
                }
        except Exception:
            pass  # If file is corrupted, start fresh


def _save_cache_to_file():
    """Persist current in-memory translations to JSON cache file."""
    try:
        _ensure_cache_dir()
        translations_list = [
            [text, lang, translated]
            for (text, lang), translated in TRANSLATION_CACHE.items()
        ]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'translations': translations_list}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Silently fail if unable to write


# Load cache at module import
_load_cache_from_file()


def get_random_language():
    """
    Return a random language code from LANGUAGES list.

    Returns:
        str: Random language code.
    """
    return random.choice(LANGUAGES)


def _can_translate(target_lang: str) -> bool:
    """
    Check if translation is possible for the given target language.

    Args:
        target_lang (str): Target language code.

    Returns:
        bool: True if Azure credentials and endpoint exist and language is translatable.
    """
    if not target_lang or target_lang == "en":
        return False
    if not AZURE_KEY or not AZURE_REGION:
        return False
    endpoint = (AZURE_ENDPOINT or "").strip()
    if not endpoint:
        return False
    return True


def _normalized_endpoint() -> str:
    """
    Return the normalized Azure Translator endpoint URL.

    Returns:
        str: Endpoint URL starting with https:// or empty string if invalid.
    """
    endpoint = (AZURE_ENDPOINT or "").strip()
    if not endpoint:
        return ""
    if not endpoint.startswith("http"):
        endpoint = "https://" + endpoint.lstrip("/")
    return endpoint


def translate(text: str, target_lang: str) -> str:
    """
    Translate a single string using Azure Translator with caching.

    Args:
        text (str): Original text to translate.
        target_lang (str): Language code to translate to.

    Returns:
        str: Translated text, or original text if translation is skipped or fails.

    Notes:
        - Skips translation if target_lang is "en" or Azure credentials are missing.
        - Uses in-memory and file cache to avoid repeated API calls.
    """
    if not text or target_lang == "en":
        return text

    if not _can_translate(target_lang):
        return text
    endpoint = _normalized_endpoint()

    cache_key = (text, target_lang)
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]

    url = f"{endpoint}/translate?api-version=3.0&to={target_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_REGION,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }

    try:
        response = requests.post(url, headers=headers, json=[{"text": text}], timeout=2.5)
        response.raise_for_status()
        translated = response.json()[0]["translations"][0]["text"]
    except Exception:
        return text

    TRANSLATION_CACHE[cache_key] = translated
    _save_cache_to_file()
    return translated


def translate_many(texts, target_lang):
    """
    Batch translate multiple strings using Azure Translator with caching.

    Args:
        texts (iterable of str): Strings to translate.
        target_lang (str): Language code to translate to.

    Returns:
        dict: Mapping of original text to translated text.

    Notes:
        - Skips translation for empty list, target_lang="en", or missing credentials.
        - Uses in-memory and file cache to minimize API calls.
        - Returns original text if translation fails.
    """
    texts = list(dict.fromkeys(t for t in texts if t))  # unique, preserve order
    if not texts or target_lang == "en" or not _can_translate(target_lang):
        return {t: t for t in texts}

    endpoint = _normalized_endpoint()
    
    result = {}
    uncached_texts = []
    for text in texts:
        cache_key = (text, target_lang)
        if cache_key in TRANSLATION_CACHE:
            result[text] = TRANSLATION_CACHE[cache_key]
        else:
            uncached_texts.append(text)
    
    if not uncached_texts:
        return result
    
    try:
        payload = [{"text": t} for t in uncached_texts]
        response = requests.post(
            f"{endpoint}/translate?api-version=3.0&to={target_lang}",
            headers={
                "Ocp-Apim-Subscription-Key": AZURE_KEY,
                "Ocp-Apim-Subscription-Region": AZURE_REGION,
                "Content-Type": "application/json",
                "X-ClientTraceId": str(uuid.uuid4()),
            },
            json=payload,
            timeout=3.0,
        )
        response.raise_for_status()
        data = response.json()
        translated_texts = [item["translations"][0]["text"] for item in data]
        
        for orig, trans in zip(uncached_texts, translated_texts):
            cache_key = (orig, target_lang)
            TRANSLATION_CACHE[cache_key] = trans
            result[orig] = trans
        
        _save_cache_to_file()
        return result
    except Exception:
        for t in uncached_texts:
            result[t] = t
        return result
