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
MIN_LOCAL_MATERIAL_EDGE = 470  # mpt==1.3.9 allows 10px tolerance below 480px.
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
    has_local_materials: bool = False, needs_ai: bool = True,
) -> list[str]:
    issues = []
    if needs_ai and llm_provider == "codex_app_server":
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
        issues.append("ローカル素材がありません。動画または画像をアップロードしてください。")
    return issues


def needs_text_ai(script: str, terms: str, video_source: str) -> bool:
    return not str(script or "").strip() or (
        video_source != "local" and not str(terms or "").strip()
    )


def first_video_steps(
    *, subject: str, script: str, terms: str, video_source: str,
    provider: str, app_config, executable, logged_in: bool,
    has_local_materials: bool, local_material_valid: bool = True,
) -> list[tuple[str, bool | None, str]]:
    """Describe only the inputs this particular first video will use."""
    has_script = bool(str(script or "").strip())
    has_topic = bool(str(subject or "").strip())
    needs_ai = needs_text_ai(script, terms, video_source)
    steps = [(
        "1. 題材または台本",
        has_topic or has_script,
        "題材を入力するとAIが台本を作ります。台本を自分で入力することもできます。",
    )]
    if needs_ai:
        if provider == "codex_app_server":
            ready = bool(executable and logged_in)
            detail = (
                "台本や素材の検索語を作るため、Mac miniのCodexログインを使います。"
                "未ログインならMac miniで `codex login` を一度実行してください。"
            )
        else:
            ready = None  # Other providers have their own setup checks in the settings pane.
            detail = (
                "台本や素材の検索語に、選択中の文章AIを使います。"
                "初回は「文章モデル設定」で、このサービスの接続を確認してください。"
            )
        steps.append(("2. 文章AI", ready, detail))
    else:
        steps.append((
            "2. 文章AI", True,
            "入力済みの台本と素材" + (
                "" if video_source == "local" else "検索語"
            ) + "を使うため、この動画では文章AIの呼び出しは不要です。",
        ))

    material = MATERIAL_KEYS.get(video_source)
    if video_source == "local":
        ready = has_local_materials and local_material_valid
        detail = (
            "自分の動画・画像をアップロードします。素材サービスの登録やAPIキーは不要です。"
            "画像は縦横480px以上の元画像を使ってください。"
        )
    elif material:
        key, service = material
        ready = has_configured_key(app_config.get(key))
        detail = (
            f"{service}の既存動画を探します。このサービスを選んだ場合だけ、"
            "素材設定にAPIキーが必要です。"
        )
    else:
        ready = None  # Detailed credential and charge checks are owned by the selected provider.
        detail = (
            "選択中のサービスで素材を生成します。サービス別の説明で"
            "登録・キー・料金を確認してください。追加費用がかかる場合があります。"
        )
    steps.append(("3. 映像素材", ready, detail))
    return steps


OPTIONAL_FEATURES = (
    ("声・読み上げ速度", "聞こえる声やテンポが変わります。既定のEdge TTSならキー不要。別の音声サービスを選んだ場合だけ、その接続設定が必要です。"),
    ("BGM", "雰囲気を変えます。無音も選べます。SoniloやElevenLabsを選んだ場合だけ、そのサービスの設定が必要です。"),
    ("字幕・字体・位置", "画面の読みやすさを調整します。既定の字幕設定で始められます。不要なら字幕をオフにできます。"),
    ("画面比率・素材の並び・切り替え効果", "縦型か横型か、素材の順序、場面の切り替わり方が変わります。外部サービスの登録は不要です。"),
    ("生成する本数", "同じ設定から複数の動画を作ります。まずは1本のままで十分です。"),
    ("文章モデル・モデル名", "台本や素材検索語の作り方が変わります。映像生成モデルの切り替えではありません。Codexはモデル名を空欄にすると既定モデルを使います。"),
    ("AI動画・AI画像の素材サービス", "手持ちの素材や既存動画の代わりに、新しい映像・画像を作ります。選んだサービスの登録、キー、料金確認が必要です。"),
)


def render_readiness(
    video_source: str, app_config, has_local_materials: bool, open_settings,
    *, subject="", script="", terms="", uploaded_files=None, saved_materials=None,
) -> bool:
    import streamlit as st

    provider = st.session_state.get("llm_provider_select") or app_config.get("llm_provider", "")
    executable = shutil.which(os.environ.get("MPT_CODEX_CLI", "codex"))
    logged_in = False
    if executable and provider == "codex_app_server" and needs_text_ai(script, terms, video_source):
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
        needs_ai=needs_text_ai(script, terms, video_source),
    )
    if not str(subject or "").strip() and not str(script or "").strip():
        issues.insert(0, "題材または台本を入力してください。どちらか一方で始められます。")
    material_issues = (
        local_material_resolution_issues(uploaded_files, saved_materials)
        if video_source == "local" else []
    )
    issues.extend(material_issues)

    with st.container(border=True):
        st.markdown("**最初の1本：確認するのは3つだけ**")
        st.caption("使わないサービスの登録やAPIキーは不要です。まず1本作り、必要になった機能だけ後から変更できます。")
        for title, ready, detail in first_video_steps(
            subject=subject, script=script, terms=terms, video_source=video_source,
            provider=provider, app_config=app_config, executable=executable,
            logged_in=logged_in, has_local_materials=has_local_materials,
            local_material_valid=not material_issues,
        ):
            icon = "🔎" if ready is None else ("✅" if ready else "⚠️")
            st.markdown(f"{icon} **{title}** — {detail}")
        st.caption("音声と字幕を既定のまま使うなら、追加のサービス登録は不要です。")
        if issues:
            for issue in issues:
                st.warning(issue)
            if any("APIキー" in issue for issue in issues):
                st.button("素材の設定を開く", key="mpt_readiness_open_settings", on_click=open_settings)
        if provider == "codex_app_server" and needs_text_ai(script, terms, video_source) and st.button("Codexの接続を再確認", key="mpt_readiness_refresh"):
            st.session_state.pop("mpt_codex_login_status", None)
            st.rerun()
    with st.expander("仕上がりを変える設定：何が変わる？", expanded=False):
        st.caption("初回は表示中の値のまま進められます。変えたい効果があるときだけ調整してください。")
        for name, effect in OPTIONAL_FEATURES:
            st.markdown(f"**{name}**：{effect}")
    return bool(material_issues)
