"""Add the local setup checklist to the pinned mpt WebUI, idempotently."""

import sys
from importlib.metadata import distribution
from pathlib import Path


ANCHOR = "    _render_settings_transfer(params)\n\n    start_button = st.button(\n"
INSERTION = (
    "    _render_settings_transfer(params)\n\n"
    "    from mpt_codex.readiness import render_readiness\n"
    "    render_readiness(params.video_source, config.app, has_local_materials, _open_settings_dialog)\n\n"
    "    start_button = st.button(\n"
)
LANGUAGE_ANCHOR = '            selected_language_code = st.selectbox(\n                "Language / 语言",'
LANGUAGE_INSERTION = (
    '            if not st.session_state.get("_mpt_language_synced"):\n'
    '                saved_language = config.ui.get("language", "")\n'
    '                if saved_language in locales:\n'
    '                    st.session_state["top_language_code_selector"] = saved_language\n'
    '                st.session_state["_mpt_language_synced"] = True\n\n'
    + LANGUAGE_ANCHOR
)
TIPS_ANCHOR = '    tips_language = ui_language if ui_language in {"zh", "en"} else "en"'
TIPS_INSERTION = '    tips_language = ui_language if ui_language in {"zh", "en", "ja"} else "en"'
REGION_ANCHOR = 'prefer_international=tips_language == "en"'
REGION_INSERTION = 'prefer_international=tips_language != "zh"'


def patch_text(source: str) -> str:
    if source.count(INSERTION) != 1 and source.count(ANCHOR) != 1:
        raise ValueError("mpt WebUI layout changed; cannot place setup checklist")
    if source.count(LANGUAGE_INSERTION) != 1 and source.count(LANGUAGE_ANCHOR) != 1:
        raise ValueError("mpt WebUI layout changed; cannot preserve selected language")
    if source.count(TIPS_INSERTION) != 2 and source.count(TIPS_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot enable Japanese provider tips")
    if source.count(REGION_INSERTION) != 2 and source.count(REGION_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot preserve international endpoints")
    if source.count(INSERTION) != 1:
        source = source.replace(ANCHOR, INSERTION, 1)
    if source.count(LANGUAGE_INSERTION) != 1:
        source = source.replace(LANGUAGE_ANCHOR, LANGUAGE_INSERTION, 1)
    if source.count(TIPS_INSERTION) != 2:
        source = source.replace(TIPS_ANCHOR, TIPS_INSERTION)
    if source.count(REGION_INSERTION) != 2:
        source = source.replace(REGION_ANCHOR, REGION_INSERTION)
    return source


def main() -> None:
    if distribution("mpt").version != "1.3.8":
        raise SystemExit("setup checklist requires mpt==1.3.8")
    target = Path(distribution("mpt").locate_file("webui/Main.py"))
    source = target.read_text(encoding="utf-8")
    patched = patch_text(source)
    if sys.argv[1:] == ["--check"]:
        print("WebUI setup checklist patch is compatible")
    elif len(sys.argv) != 1:
        raise SystemExit("usage: patch-webui.py [--check]")
    elif source != patched:
        target.write_text(patched, encoding="utf-8")
        print("WebUI setup checklist installed")
    else:
        print("WebUI setup checklist already installed")


if __name__ == "__main__":
    main()
