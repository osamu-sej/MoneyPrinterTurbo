"""Small, actionable setup checks beside the video generation button."""

import os
import shutil
import subprocess
import time
from io import BytesIO
from pathlib import Path


MATERIAL_KEYS = {
    "pexels": ("pexels_api_keys", "Pexels"),
    "pixabay": ("pixabay_api_keys", "Pixabay"),
    "coverr": ("coverr_api_keys", "Coverr"),
    "wavespeed": ("wavespeed_api_keys", "WaveSpeed"),
}
MIN_LOCAL_MATERIAL_EDGE = 470  # mpt==1.3.8 allows 10px tolerance below 480px.
LOCAL_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def local_material_resolution_issues(uploaded_files, saved_materials) -> list[str]:
    """Check selected images before the task spends time generating audio."""
    from PIL import Image

    issues = []
    if uploaded_files:
        images = (
            (Path(item.name).name, BytesIO(item.getvalue()))
            for item in uploaded_files
            if Path(item.name).suffix.lower() in LOCAL_IMAGE_EXTENSIONS
        )
    else:
        images = (
            ("前回アップロードした画像", str(item.get("url") or ""))
            for item in saved_materials or []
            if Path(str(item.get("url") or "")).suffix.lower() in LOCAL_IMAGE_EXTENSIONS
        )

    for label, source in images:
        try:
            if not uploaded_files:
                from app.utils import file_security, utils

                source = file_security.resolve_path_within_directory(
                    utils.storage_dir("local_videos", create=False), source
                )
            with Image.open(source) as image:
                width, height = image.size
        except (OSError, ValueError):
            issues.append(f"{label} を読み取れません。画像を選び直してください。")
            continue
        if width < MIN_LOCAL_MATERIAL_EDGE or height < MIN_LOCAL_MATERIAL_EDGE:
            issues.append(
                f"{label} は {width}×{height}px です。縦横とも480px以上の元画像を選んでください。"
            )
    return issues


def has_configured_key(value) -> bool:
    if isinstance(value, (list, tuple, set)):
        return any(str(item or "").strip() for item in value)
    return bool(str(value or "").strip())


def codex_logged_in(executable: str) -> bool:
    """Check credentials without printing the command output or token data."""
    try:
        result = subprocess.run(
            [executable, "login", "status"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def setup_issues(
    video_source: str, llm_provider: str, app_config, *, executable, logged_in,
    has_local_materials: bool = False,
) -> list[str]:
    issues = []
    if llm_provider == "codex_app_server":
        if not executable:
            issues.append("Codex CLIが見つかりません。Mac miniにCodex CLIを導入してください。")
        elif not logged_in:
            issues.append("Codexにログインしていません。Mac miniのターミナルで `codex login` を実行してください。")

    material = MATERIAL_KEYS.get(video_source)
    if material:
        key, service = material
        if not has_configured_key(app_config.get(key)):
            issues.append(f"{service}のAPIキーが未設定です。「設定」で入力してください。")
    if video_source == "local" and not has_local_materials:
        issues.append("ローカル素材がありません。動画ファイルをアップロードしてください。")
    return issues


def render_readiness(
    video_source: str, app_config, has_local_materials: bool, open_settings,
    *, uploaded_files=None, saved_materials=None,
) -> bool:
    import streamlit as st

    provider = st.session_state.get("llm_provider_select") or app_config.get("llm_provider", "")
    executable = shutil.which(os.environ.get("MPT_CODEX_CLI", "codex"))
    logged_in = False
    if executable and provider == "codex_app_server":
        cached = st.session_state.get("mpt_codex_login_status")
        now = time.monotonic()
        if cached and cached[0] == executable and now - cached[1] < 60:
            logged_in = cached[2]
        else:
            logged_in = codex_logged_in(executable)
            st.session_state["mpt_codex_login_status"] = (executable, now, logged_in)
    issues = setup_issues(
        video_source, provider, app_config, executable=executable, logged_in=logged_in,
        has_local_materials=has_local_materials,
    )
    material_issues = (
        local_material_resolution_issues(uploaded_files, saved_materials)
        if video_source == "local" else []
    )
    issues.extend(material_issues)

    heading = "生成前の確認：設定が必要です" if issues else "生成前の確認：基本設定OK"
    with st.expander(heading, expanded=bool(issues)):
        if issues:
            for issue in issues:
                st.warning(issue)
            if any("APIキー" in issue for issue in issues):
                st.button("設定を開く", key="mpt_readiness_open_settings", on_click=open_settings)
        else:
            st.success("確認対象の設定はそろっています。")
        if video_source not in MATERIAL_KEYS and video_source != "local":
            st.caption("この素材ソースの個別設定や料金確認は、素材設定欄で確認してください。")
        if st.button("接続を再確認", key="mpt_readiness_refresh"):
            st.session_state.pop("mpt_codex_login_status", None)
            st.rerun()
    return bool(material_issues)
