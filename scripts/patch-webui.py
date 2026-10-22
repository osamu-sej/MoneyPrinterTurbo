"""Add the generation setup checklist to the pinned mpt WebUI, idempotently."""

import sys
from importlib.metadata import distribution
from pathlib import Path


ANCHOR = "    _render_settings_transfer(params)\n\n    start_button = st.button(\n"
INSERTION = (
    "    _render_settings_transfer(params)\n\n"
    "    from mpt_codex.readiness import render_readiness\n"
    "    generation_blocked = render_readiness(\n"
    "        params.video_source, config.app, has_local_materials, _open_settings_dialog,\n"
    "        subject=params.video_subject, script=params.video_script, terms=params.video_terms,\n"
    "        uploaded_files=uploaded_files,\n"
    "        saved_materials=st.session_state.get(\"local_video_materials\", []),\n"
    "    )\n\n"
    "    start_button = st.button(\n"
)
CURRENT_INSERTION = INSERTION.replace("generation_blocked", "local_resolution_blocked")
PREVIOUS_INSERTION = INSERTION.replace(
    "        subject=params.video_subject, script=params.video_script, terms=params.video_terms,\n",
    "",
)
CURRENT_PREVIOUS_INSERTION = PREVIOUS_INSERTION.replace(
    "generation_blocked", "local_resolution_blocked"
)
OLD_INSERTION = (
    "    _render_settings_transfer(params)\n\n"
    "    from mpt_codex.readiness import render_readiness\n"
    "    render_readiness(params.video_source, config.app, has_local_materials, _open_settings_dialog)\n\n"
    "    start_button = st.button(\n"
)
BUTTON_ANCHOR = '        key="generate_video_button",\n        on_click=_prepare_generation_task,\n'
BUTTON_INSERTION = BUTTON_ANCHOR + '        disabled=generation_blocked,\n'
CURRENT_BUTTON_INSERTION = BUTTON_ANCHOR + '        disabled=local_resolution_blocked,\n'
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
LLM_GUIDE_ANCHOR = "            tips = get_llm_provider_tips(llm_provider, **provider_tip_context)\n"
LLM_GUIDE_INSERTION = (
    "            from mpt_codex.service_guide import render_llm_guide\n"
    "            with llm_helper:\n"
    "                render_llm_guide(\n"
    "                    llm_provider_spec, selected_service_endpoint,\n"
    "                    st.session_state.get(\"ui_language\", config.ui.get(\"language\", \"\")),\n"
    "                )\n\n"
    + LLM_GUIDE_ANCHOR
)
VIDEO_GUIDE_ANCHOR = '            _set_runtime_config("app", "video_source", params.video_source)\n\n'
VIDEO_GUIDE_INSERTION = (
    VIDEO_GUIDE_ANCHOR
    + "            from mpt_codex.service_guide import render_video_guide\n"
    + "            render_video_guide(\n"
    + "                params.video_source,\n"
    + '                st.session_state.get("ui_language", config.ui.get("language", "")),\n'
    + "            )\n\n"
)
AUDIO_GUIDE_ANCHOR = (
    "            if tts_mode_enabled:\n"
    "                provider_tips = get_tts_provider_tips(selected_tts_server)\n"
    "                if provider_tips:\n"
    "                    st.info(provider_tips)\n"
)
AUDIO_GUIDE_INSERTION = (
    "            if tts_mode_enabled:\n"
    "                provider_tips = get_tts_provider_tips(selected_tts_server)\n"
    "                from mpt_codex.service_guide import render_tts_guide\n"
    "                render_tts_guide(\n"
    "                    selected_tts_server, provider_tips,\n"
    '                    st.session_state.get("ui_language", config.ui.get("language", "")),\n'
    "                )\n"
)
# The upstream comment is Chinese. Keep the exact first line as the stable anchor.
MATERIAL_DIRECTORY_ANCHOR = "        with right_config_panel:\n            # 素材 Provider 按「搜索库存素材 / AI 生成视频 / AI 生成图片」\n"
MATERIAL_DIRECTORY_INSERTION = (
    "        with right_config_panel:\n"
    "            from mpt_codex.service_guide import render_material_directory\n"
    "            render_material_directory(\n"
    '                st.session_state.get("ui_language", config.ui.get("language", ""))\n'
    "            )\n"
    "            # 素材 Provider 按「搜索库存素材 / AI 生成视频 / AI 生成图片」\n"
)
SECTION_INTRO_ANCHORS = {
    "script": '            st.write(tr("Video Script Settings"))\n',
    "video": '            st.write(tr("Video Settings"))\n',
    "audio": '            st.write(tr("Audio Settings"))\n',
    "subtitle": '            st.write(tr("Subtitle Settings"))\n',
}
FAILED_TASK_ANCHOR = (
    '        error = str(task.get("error") or "").strip()\n'
    '        message = tr("Video Generation Failed")\n'
    '        st.error(f"{message}: {error}" if error else message)\n'
)
FAILED_TASK_INSERTION = (
    "        from mpt_codex.failure_guidance import render_failure_guidance\n"
    "        render_failure_guidance(task)\n"
)
TASK_SUMMARY_ANCHOR = (
    '            "state": task.get("state"),\n'
    '            "cross_post_state": task.get("cross_post_state"),\n'
)
TASK_SUMMARY_INSERTION = (
    '            "state": task.get("state"),\n'
    '            "failed_stage": task.get("failed_stage"),\n'
    '            "error": task.get("error"),\n'
    '            "remote_job_exists": any(task.get(key) for key in (\n'
    '                "loomloom_run_id", "volcengine_seedance_task_id",\n'
    '                "wavespeed_prediction_id", "ofox_task_id",\n'
    '                "metaso_minimax_task_id", "muapi_task_id",\n'
    '            )),\n'
    '            "cross_post_state": task.get("cross_post_state"),\n'
)
TASK_ROW_ANCHOR = (
    '                        else:\n'
    '                            st.error(tr("Task Delete Failed"))\n\n\n'
    'def _render_task_manager_panel(tasks=None):\n'
)
TASK_ROW_INSERTION = (
    '                        else:\n'
    '                            st.error(tr("Task Delete Failed"))\n\n'
    '                if _task_state_filter_key(task) == "failed":\n'
    '                    from mpt_codex.failure_guidance import render_failure_guidance\n'
    '                    render_failure_guidance(task, compact=True)\n\n\n'
    'def _render_task_manager_panel(tasks=None):\n'
)


def section_intro_insertion(section: str, anchor: str) -> str:
    return (
        anchor
        + "            from mpt_codex.service_guide import render_section_intro\n"
        + f'            render_section_intro("{section}", st.session_state.get("ui_language", config.ui.get("language", "")))\n'
    )


def patch_text(source: str) -> str:
    if sum(source.count(value) for value in (INSERTION, CURRENT_INSERTION, PREVIOUS_INSERTION, CURRENT_PREVIOUS_INSERTION, OLD_INSERTION, ANCHOR)) != 1:
        raise ValueError("mpt WebUI layout changed; cannot place setup checklist")
    patched_buttons = source.count(BUTTON_INSERTION) + source.count(CURRENT_BUTTON_INSERTION)
    if patched_buttons != 1 and not (patched_buttons == 0 and source.count(BUTTON_ANCHOR) == 1):
        raise ValueError("mpt WebUI layout changed; cannot block incomplete setup")
    if source.count(LANGUAGE_INSERTION) != 1 and source.count(LANGUAGE_ANCHOR) != 1:
        raise ValueError("mpt WebUI layout changed; cannot preserve selected language")
    if source.count(TIPS_INSERTION) != 2 and source.count(TIPS_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot enable Japanese provider tips")
    if source.count(REGION_INSERTION) != 2 and source.count(REGION_ANCHOR) != 2:
        raise ValueError("mpt WebUI layout changed; cannot preserve international endpoints")
    for name, old, new in (
        ("LLM guide", LLM_GUIDE_ANCHOR, LLM_GUIDE_INSERTION),
        ("video guide", VIDEO_GUIDE_ANCHOR, VIDEO_GUIDE_INSERTION),
        ("voice guide", AUDIO_GUIDE_ANCHOR, AUDIO_GUIDE_INSERTION),
        ("material directory", MATERIAL_DIRECTORY_ANCHOR, MATERIAL_DIRECTORY_INSERTION),
    ):
        if source.count(new) != 1 and source.count(old) != 1:
            raise ValueError(f"mpt WebUI layout changed; cannot place {name}")
    for section, anchor in SECTION_INTRO_ANCHORS.items():
        insertion = section_intro_insertion(section, anchor)
        if source.count(insertion) != 1 and source.count(anchor) != 1:
            raise ValueError(f"mpt WebUI layout changed; cannot place {section} introduction")
    for name, old, new in (
        ("failure guidance", FAILED_TASK_ANCHOR, FAILED_TASK_INSERTION),
        ("failure summary", TASK_SUMMARY_ANCHOR, TASK_SUMMARY_INSERTION),
        ("task row guidance", TASK_ROW_ANCHOR, TASK_ROW_INSERTION),
    ):
        if source.count(new) != 1 and source.count(old) != 1:
            raise ValueError(f"mpt WebUI layout changed; cannot place {name}")
    if source.count(CURRENT_INSERTION) == 1:
        source = source.replace(CURRENT_INSERTION, INSERTION, 1)
    elif source.count(CURRENT_PREVIOUS_INSERTION) == 1:
        source = source.replace(CURRENT_PREVIOUS_INSERTION, INSERTION, 1)
    elif source.count(PREVIOUS_INSERTION) == 1:
        source = source.replace(PREVIOUS_INSERTION, INSERTION, 1)
    elif source.count(OLD_INSERTION) == 1:
        source = source.replace(OLD_INSERTION, INSERTION, 1)
    elif source.count(INSERTION) != 1:
        source = source.replace(ANCHOR, INSERTION, 1)
    if source.count(CURRENT_BUTTON_INSERTION) == 1:
        source = source.replace(CURRENT_BUTTON_INSERTION, BUTTON_INSERTION, 1)
    elif source.count(BUTTON_INSERTION) != 1:
        source = source.replace(BUTTON_ANCHOR, BUTTON_INSERTION, 1)
    if source.count(LANGUAGE_INSERTION) != 1:
        source = source.replace(LANGUAGE_ANCHOR, LANGUAGE_INSERTION, 1)
    if source.count(TIPS_INSERTION) != 2:
        source = source.replace(TIPS_ANCHOR, TIPS_INSERTION)
    if source.count(REGION_INSERTION) != 2:
        source = source.replace(REGION_ANCHOR, REGION_INSERTION)
    for old, new in (
        (LLM_GUIDE_ANCHOR, LLM_GUIDE_INSERTION),
        (VIDEO_GUIDE_ANCHOR, VIDEO_GUIDE_INSERTION),
        (AUDIO_GUIDE_ANCHOR, AUDIO_GUIDE_INSERTION),
        (MATERIAL_DIRECTORY_ANCHOR, MATERIAL_DIRECTORY_INSERTION),
    ):
        if source.count(new) != 1:
            source = source.replace(old, new, 1)
    for section, anchor in SECTION_INTRO_ANCHORS.items():
        insertion = section_intro_insertion(section, anchor)
        if source.count(insertion) != 1:
            source = source.replace(anchor, insertion, 1)
    for old, new in (
        (FAILED_TASK_ANCHOR, FAILED_TASK_INSERTION),
        (TASK_SUMMARY_ANCHOR, TASK_SUMMARY_INSERTION),
        (TASK_ROW_ANCHOR, TASK_ROW_INSERTION),
    ):
        if source.count(new) != 1:
            source = source.replace(old, new, 1)
    return source


def patch_style(source: str, mobile_style: str) -> str:
    if source.count(MOBILE_STYLE_MARKER) == 1:
        return source
    if source.count(MOBILE_STYLE_MARKER) != 0:
        raise ValueError("mpt mobile stylesheet marker is duplicated")
    return source.rstrip() + "\n\n" + mobile_style.strip() + "\n"


def main() -> None:
    if distribution("mpt").version != "1.3.9":
        raise SystemExit("setup checklist requires mpt==1.3.9")
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
