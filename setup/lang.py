import json

from setup.constants import (
    LANG_FILE,
    FILE_ENCODING,
)

# =============================================================================
class Language:

    def __init__(self, language: str) -> None:

        self.language: str = language.lower()
        self._texts: dict[str, str] = self._load()

    # -------------------------------------------------------------------------
    def _load(self) -> dict[str, str]:

        with LANG_FILE.open(
            "r",
            encoding=FILE_ENCODING,
        ) as jrfile:
            
            data = json.load(jrfile)

        return {
            key: value[self.language]
            for key, value in data.items()
        }

    # -------------------------------------------------------------------------
    def get_text(self, key: str) -> str:
        if key not in self._texts.keys():
             raise RuntimeError(
                f"Key {key} does not exist in lang.json"
            )
        return self._texts[key]

    # -------------------------------------------------------------------------
    def plural(self, singular_text: str, replace_by: str | None = None) -> str:
        return (
            f"{singular_text}s" if replace_by is None else replace_by
        )

    # -------------------------------------------------------------------------
    def text_comply_with_number(self, number: int, text: str, if_plurial: str | None = None) -> str:
        return (
            self.plural(singular_text= text, replace_by = if_plurial)
            if number > 1
            else text
        )

# =============================================================================

_language: Language | None = None

# =============================================================================
def init_language(language: str) -> None:
    global _language

    _language = Language(language)

# =============================================================================
def get_text(key: str) -> str:
    if _language is None:
        raise RuntimeError(
            "Language not initialized"
        )

    return _language.get_text(key)
