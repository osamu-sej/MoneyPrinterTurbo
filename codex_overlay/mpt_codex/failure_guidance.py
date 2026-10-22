"""Japanese, actionable guidance for persisted video generation failures."""

import re
from dataclasses import dataclass
from typing import Mapping


STAGE_NAMES = {
    "preflight": "事前確認",
    "script": "台本",
    "terms": "素材検索語",
    "audio": "音声",
    "subtitle": "字幕",
    "materials": "映像素材",
    "video": "動画合成",
    "pipeline": "生成処理",
}
REMOTE_JOB_KEYS = (
    "loomloom_run_id", "volcengine_seedance_task_id", "wavespeed_prediction_id",
    "ofox_task_id", "metaso_minimax_task_id", "muapi_task_id",
)


@dataclass(frozen=True)
class FailureAdvice:
    reason: str
    actions: tuple[str, ...]
    stage: str
    detail: str
    remote_job_exists: bool = False


def _safe_detail(error: str) -> str:
    """Keep a short diagnostic hint without echoing credentials or local paths."""
    value = re.sub(r"[\x00-\x1f\x7f]+", " ", str(error or "")).strip()
    if not value:
        return ""
    if re.search(r"api[_ -]?key|token|secret|password|authorization|bearer|sk-[\w-]+", value, re.I):
        return "認証情報を含む可能性があるため、詳細表示を省略しました。"
    value = re.sub(r"https?://\S+", "[URL]", value, flags=re.I)
    value = re.sub(r"(?:/Users/|/home/|/private/|[A-Za-z]:\\)\S+", "[ローカルパス]", value)
    return value[:240] + ("…" if len(value) > 240 else "")


def diagnose_failure(task: Mapping) -> FailureAdvice:
    """Use recorded stage and error; do not infer a specific cause from stage alone."""
    stage_key = str(task.get("failed_stage") or "").lower()
    stage = STAGE_NAMES.get(stage_key, "不明な段階")
    error = str(task.get("error") or "").strip()
    lowered = error.lower()
    remote_job_exists = bool(task.get("remote_job_exists")) or any(
        task.get(key) for key in REMOTE_JOB_KEYS
    )

    if "low resolution material" in lowered or "no valid local video materials" in lowered:
        reason = "選んだローカル素材を動画に使用できませんでした。画像サイズやファイル形式を確認してください。"
        actions = ("画像は縦横480px以上の元画像に替え、動画も再生できるファイルを選び直してください。",)
    elif "codex cli is not installed" in lowered:
        reason = "Mac miniでCodex CLIを見つけられません。"
        actions = ("Mac miniにCodex CLIを導入し、ターミナルで `codex login` を完了してください。",)
    elif "codex app-server has no available model" in lowered:
        reason = "Codexで利用できる文章モデルが見つかりません。"
        actions = ("Mac miniで `codex login` を確認し、文章モデル設定のモデル名を空欄にして再試行してください。",)
    elif "codex app-server stopped" in lowered or "codex app-server closed its output" in lowered:
        reason = "Codexとの接続が途中で終了しました。"
        actions = ("Mac miniでCodexのログイン状態を確認し、アプリを再起動してから試してください。",)
    elif "ffmpeg is not available" in lowered:
        reason = "動画・音声の処理に必要なFFmpegが見つかりません。"
        actions = ("Mac miniのFFmpeg設定を確認し、アプリを再起動してから試してください。",)
    elif "no space left on device" in lowered or "disk full" in lowered:
        reason = "Mac miniの保存先に空き容量が足りません。"
        actions = ("Mac miniの空き容量を確保し、不要な生成済みファイルを整理してから試してください。",)
    elif "permission denied" in lowered or "operation not permitted" in lowered:
        reason = "Mac miniが必要なファイルまたは保存先にアクセスできません。"
        actions = ("素材と保存先のアクセス権を確認し、使えるフォルダに素材を置き直してください。",)
    elif re.search(r"\b(401|403|unauthorized|forbidden)\b|not logged|login required|requires? (?:an? )?api key|invalid api key", lowered):
        reason = "選択したサービスの認証または利用権限を確認できませんでした。"
        actions = ("「設定」で選択中のサービスの接続を確認してください。Codexを使う場合はMac miniで `codex login` を確認してください。",)
    elif re.search(r"\b429\b|rate limit|quota|insufficient credits|insufficient balance", lowered):
        reason = "サービスの利用枠・残高、または一時的な回数制限に達した可能性があります。"
        actions = ("サービスの管理画面で利用枠と残高を確認し、回数制限なら時間を置いてください。",)
    elif re.search(r"timed? out|timeout|connection|\bdns\b|enotfound|temporarily unavailable|\b503\b", lowered):
        reason = "外部サービスとの通信が完了しませんでした。"
        actions = ("Mac miniのネットワークと選択中のサービスの稼働状況を確認してください。",)
    elif "failed to download video materials" in lowered:
        reason = "選択したサービスから映像素材を取得できませんでした。"
        actions = ("素材サービスの設定と検索語を確認し、別の検索語またはローカル素材で試してください。",)
    elif "failed to synthesize audio" in lowered or "audio duration is zero" in lowered:
        reason = "音声を作成できないか、音声ファイルの長さが0秒でした。"
        actions = ("選択中の声と音声サービスの接続を確認してください。アップロード音声なら再生できるファイルに替えてください。",)
    elif not error:
        reason = "失敗の詳細が保存されていません。"
        actions = ("タスクのログを確認してください。再発する場合はタスクIDと発生時刻を控えてください。",)
    else:
        reason = f"{stage}の処理中に停止しました。記録だけでは原因を特定できません。"
        stage_actions = {
            "script": "文章モデルの設定と接続を確認してください。",
            "terms": "文章モデルの設定と素材検索語を確認してください。",
            "audio": "音声設定と入力音声ファイルを確認してください。",
            "subtitle": "字幕設定を確認してください。字幕を使わない動画なら字幕をオフにして試せます。",
            "materials": "素材の設定、検索語、アップロードしたファイルを確認してください。",
            "video": "素材ファイルとMac miniの空き容量を確認し、まず1本で試してください。",
            "preflight": "設定画面で選択中のサービスの必須項目を確認してください。",
        }
        actions = (stage_actions.get(stage_key, "タスクのログで停止箇所を確認してください。"),)

    return FailureAdvice(reason, actions, stage, _safe_detail(error), remote_job_exists)


def render_failure_guidance(task: Mapping, *, compact: bool = False) -> None:
    import streamlit as st

    advice = diagnose_failure(task)
    if compact:
        st.caption(f"失敗理由：{advice.reason}")
        container = st.expander("改善方法とエラー詳細", expanded=False)
    else:
        st.error(f"動画生成に失敗しました：{advice.reason}")
        container = st.container()
    with container:
        st.caption(f"停止した段階：{advice.stage}")
        if advice.remote_job_exists:
            st.warning("有料の生成依頼がサービス側で続いている可能性があります。再試行前にサービスの管理画面で結果を確認してください。")
        st.markdown("**次に試すこと**")
        for action in advice.actions:
            st.markdown(f"- {action}")
        if advice.detail:
            st.caption(f"記録されたエラー：{advice.detail}")
