"""
Module de traduction ErgoVeille (Section 8 du cahier des charges).
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "").strip()
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
MYMEMORY_API_URL = "https://api.mymemory.translated.net/get"

_cache = {}


def _is_deepl_available():
    return bool(DEEPL_API_KEY) and ":" in DEEPL_API_KEY


def translate_deepl(text: str):
    """Retourne le texte traduit ou None en cas d'échec."""
    if not _is_deepl_available():
        return None
    if not text or len(text.strip()) < 10:
        return text
    if text in _cache:
        return _cache[text]

    try:
        # 🆕 DeepL v2 exige la clé dans l'en-tête Authorization
        headers = {
            "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
        }
        data = {
            "text": text,
            "source_lang": "EN",
            "target_lang": "FR",
        }
        response = requests.post(
            DEEPL_API_URL,
            headers=headers,
            data=data,
            timeout=15,
        )
        if response.status_code != 200:
            print(f"   ⚠️ DeepL HTTP {response.status_code}: {response.text[:200]}")
            return None
        json_data = response.json()
        translated = json_data.get("translations", [{}])[0].get("text")
        if translated:
            _cache[text] = translated
            return translated
        return None
    except Exception as e:
        print(f"   ⚠️ DeepL erreur ({type(e).__name__})")
        return None


def translate_mymemory_chunk(text: str):
    """Retourne le chunk traduit ou None."""
    if not text or len(text.strip()) < 10:
        return text
    try:
        response = requests.get(
            MYMEMORY_API_URL,
            params={"q": text[:450], "langpair": "en|fr"},
            timeout=10,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText")
        if translated and len(translated) > len(text[:450]) * 0.3:
            return translated
        return None
    except Exception:
        return None


def translate_mymemory(text: str):
    """Fallback MyMemory avec chunks."""
    if not text or len(text.strip()) < 10:
        return text
    if text in _cache:
        return _cache[text]

    chunks = [text[i:i+450] for i in range(0, len(text), 450)]
    translated_chunks = []
    
    for chunk in chunks:
        for attempt in range(2):
            result = translate_mymemory_chunk(chunk)
            if result:
                translated_chunks.append(result)
                break
            if attempt == 0:
                time.sleep(1)
        else:
            # Échec total → on garde le chunk original
            translated_chunks.append(chunk)
        time.sleep(0.3)
    
    translated = "".join(translated_chunks)
    _cache[text] = translated
    return translated


def traduire_texte(texte: str) -> str:
    """
    Traduit un texte. Retourne TOUJOURS une chaîne (jamais None).
    En cas d'échec total, retourne le texte original.
    """
    if not texte or len(texte.strip()) < 10:
        return texte
    
    # Essayer DeepL
    if _is_deepl_available():
        result = translate_deepl(texte)
        if result:
            return result
    
    # Fallback MyMemory
    result = translate_mymemory(texte)
    if result:
        return result
    
    # Échec total → texte original
    return texte


def est_traduction_active(config: dict) -> bool:
    return bool(config.get("newsletter", {}).get("traduction_active", False))