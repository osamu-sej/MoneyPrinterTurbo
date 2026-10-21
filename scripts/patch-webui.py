"""Add the local setup checklist to the pinned mpt WebUI, idempotently."""

import sys
from importlib.metadata import distribution
from pathlib import Path


ANCHOR = "    _render_settings_transfer(params)\n\n    start_button = st.button(\n"
INSERTION = (
    "    _render_settings_transfer(params)\n\n"
    "    from mpt_codex.readiness import render_readiness\n"
    "    local_resolution_blocked = render_readiness(\n"
    "        params.video_source, config.app, has_local_materials, _open_settings_dialog,\n"
    "        uploaded_files=uploaded_files,\n"
    "        saved_materials=st.session_state.get(\"local_video_materials\", []),\n"
    "    )\n\n"
    "    start_button = st.button(\n"
)
OLD_INSERTION = (
    "    _render_settings_transfer(params)\n\n"
    "    from mpt_codex.readiness import render_readiness\n"
    "    render_readiness(params.video_source, config.app, has_local_materials, _open_settings_dialog)\n\n"
    "    start_button = st.button(\n"
)
BUTTON_ANCHOR = '        key="generate_video_button",\n        on_click=_prepare_generation_task,\n'
BUTTON_INSERTION = BUTTON_ANCHOR + '        disabled=local_resolution_blocked,\n'
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
MOBILE_STYLE_MARKER = "/* mpt-mobile-v1:"


def patch_text(source: str) -> str:
    if sum(source.count(value) for value in (INSERTION, OLD_INSERTION, ANCHOR)) != 1:
        raise ValueError("mpt WebUI layout changed; cannot place setup checklist")
    if source.count(BUTTON_INSERTION) != 1 and source.count(BUTTON_ANCHOR) != 1:
        raise ValueError("mpt WebUI layout changed; cannot block low-resolution material")
    if source.count(LANGUAGE_INSERTION) != 1 and source.count(LANGUAGE_ANCHOR) != 1:
        raise ValueError("mpt WebUI layout changed; cannot preserve selected language")
    if source.count(TIPS_INSERTION) != 2 and source.count(TIPS_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot enable Japanese provider tips")
    if source.count(REGION_INSERTION) != 2 and source.count(REGION_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot preserve international endpoints")
    if source.count(OLD_INSERTION) == 1:
        source = source.replace(OLD_INSERTION, INSERTION, 1)
    elif source.count(INSERTION) != 1:
        source = source.replace(ANCHOR, INSERTION, 1)
    if source.count(BUTTON_INSERTION) != 1:
        source = source.replace(BUTTON_ANCHOR, BUTTON_INSERTION, 1)
    if source.count(LANGUAGE_INSERTION) != 1:
        source = source.replace(LANGUAGE_ANCHOR, LANGUAGE_INSERTION, 1)
    if source.count(TIPS_INSERTION) != 2:
        source = source.replace(TIPS_ANCHOR, TIPS_INSERTION)
    if source.count(REGION_INSERTION) != 2:
        source = source.replace(REGION_ANCHOR, REGION_INSERTION)
    return source


def patch_style(source: str, mobile_style: str) -> str:
    if source.count(MOBILE_STYLE_MARKER) == 1:
        return source
    if source.count(MOBILE_STYLE_MARKER) != 0:
        raise ValueError("mpt mobile stylesheet marker is duplicated")
    return source.rstrip() + "\n\n" + mobile_style.strip() + "\n"


def main() -> None:
    if distribution("mpt").version != "1.3.8":
        raise SystemExit("setup checklist requires mpt==1.3.8")
    target = Path(distribution("mpt").locate_file("webui/Main.py"))
    source = target.read_text(encoding="utf-8")
    patched = patch_text(source)
    style_target = target.with_name("styles.css")
    style_source = style_target.read_text(encoding="utf-8")
    mobile_style = (Path(__file__).resolve().parent.parent / "webui" / "mobile.css").read_text(encoding="utf-8")
    patched_style = patch_style(style_source, mobile_style)
    if sys.argv[1:] == ["--check"]:
        print("WebUI setup checklist patch is compatible")
    elif len(sys.argv) != 1:
        raise SystemExit("usage: patch-webui.py [--check]")
    elif source != patched:
        target.write_text(patched, encoding="utf-8")
        if style_source != patched_style:
            style_target.write_text(patched_style, encoding="utf-8")
        print("WebUI usability and mobile layout installed")
    else:
        if style_source != patched_style:
            style_target.write_text(patched_style, encoding="utf-8")
            print("WebUI mobile layout installed")
        else:
            print("WebUI usability and mobile layout already installed")


if __name__ == "__main__":
    main()
