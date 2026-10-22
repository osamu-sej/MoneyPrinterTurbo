"""Install the bundled Japanese UI strings into mpt 1.3.9's WebUI package."""

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path


def markers(value: str) -> tuple[list[str], list[str], list[str]]:
    placeholders = sorted(re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", value))
    urls = sorted(
        match.rstrip("`.,、，;。:")
        for match in re.findall(r"https?://[^\s)`]+", value)
    )
    code = sorted(re.findall(r"`[^`]+`", value))
    return placeholders, urls, code


def main() -> None:
    source = Path(__file__).resolve().parent.parent / "locales" / "ja.json"
    spec = importlib.util.find_spec("webui")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("mpt WebUI package was not found")
    locale_dir = Path(next(iter(spec.submodule_search_locations))) / "i18n"
    english = json.loads((locale_dir / "en.json").read_text(encoding="utf-8"))["Translation"]
    japanese_data = json.loads(source.read_text(encoding="utf-8"))
    japanese = japanese_data["Translation"]
    if japanese_data.get("Language") != "日本語":
        raise SystemExit("invalid Japanese language name")
    if set(japanese) != set(english):
        raise SystemExit(
            f"translation keys differ: missing={len(set(english)-set(japanese))} "
            f"extra={len(set(japanese)-set(english))}"
        )
    for key, original in english.items():
        translated = japanese[key]
        if not isinstance(translated, str) or not translated.strip():
            raise SystemExit(f"empty Japanese translation: {key}")
        if markers(original) != markers(translated):
            raise SystemExit(f"format marker changed: {key}")
    if sys.argv[1:] == ["--check"]:
        print(f"Japanese UI validated: {len(japanese)} strings")
        return
    if len(sys.argv) != 1:
        raise SystemExit("usage: install-locale.py [--check]")
    shutil.copyfile(source, locale_dir / "ja.json")
    print(f"Japanese UI installed: {len(japanese)} strings")


if __name__ == "__main__":
    main()
