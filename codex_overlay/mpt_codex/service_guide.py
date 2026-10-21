"""Japanese, task-specific help for the provider selectors in mpt==1.3.8."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Guide:
    capability: str
    setup: str
    links: tuple[tuple[str, str], ...] = ()


VIDEO_GUIDES = {
    "pexels": Guide(
        "公開済みのストック動画をキーワードで探して使います。AIによる新規映像生成はしません。",
        "Pexelsでアカウントを作り、APIキーを取得して「素材ソース設定」に入力します。",
        (("Pexels API・キー取得", "https://www.pexels.com/api/"),),
    ),
    "pixabay": Guide(
        "公開済みのストック動画を検索して使います。",
        "Pixabayにログインし、APIページに表示されるキーを「素材ソース設定」に入力します。",
        (("Pixabay API・キー確認", "https://pixabay.com/api/docs/"),),
    ),
    "coverr": Guide(
        "Coverrの既存動画を検索して使います。",
        "CoverrでAPIキーを作成し、「素材ソース設定」に入力します。利用条件も確認してください。",
        (("Coverr Developers", "https://coverr.co/developers/"),),
    ),
    "metaso_minimax": Guide(
        "台本のキーワードからMiniMax H3の新しい短い動画クリップを生成します。",
        "METASOで利用登録とAPIキーの準備を行い、素材設定へ入力します。生成前に料金を確認してください。",
        (("METASO MiniMax H3", "https://metaso.cn/minimax-h3"),),
    ),
    "ofox": Guide(
        "OfoxAI経由で新しい動画クリップを生成します。選ぶモデルで映像の表現や費用が変わります。",
        "OfoxAIでAPIキーを取得し、モデルIDを確認して素材設定へ入力します。生成前に料金を確認してください。",
        (("OfoxAI・モデル一覧", "https://ofox.ai/"),),
    ),
    "loomloom": Guide(
        "勝算雲で動画素材を生成します。利用可能なモデルと見積もりを確認してから実行します。",
        "勝算雲のアカウントとAPIキーを準備し、素材設定へ入力します。画面上の見積もりと料金確認が必要です。",
        (("勝算雲・コンソール", "https://console.shengsuanyun.com/"),),
    ),
    "volcengine_seedance": Guide(
        "火山方舟のSeedanceで新しい動画クリップを生成します。モデルによって対応する長さや解像度が異なります。",
        "火山方舟で対象モデルを有効にし、Ark APIキーとモデルIDを素材設定へ入力します。生成前に料金を確認してください。",
        (("Ark APIキー", "https://ark.volcengine.com/region:cn-beijing/apikey"),
         ("動画生成の公式ガイド", "https://docs.volcengine.com/docs/ark/video-generation-tutorial")),
    ),
    "wavespeed": Guide(
        "WaveSpeedAI経由で新しい動画クリップを生成します。",
        "WaveSpeedAIでAPIキーを取得して素材設定へ入力します。生成前にモデルと料金を確認してください。",
        (("WaveSpeedAI", "https://wavespeed.ai/"),),
    ),
    "muapi": Guide(
        "MuAPI経由で新しい動画クリップを生成します。エンドポイントと解像度の設定が必要です。",
        "MuAPIでAPIキーを取得し、利用する動画モデルのエンドポイントを素材設定へ入力します。料金も確認してください。",
        (("MuAPI・APIキー", "https://muapi.ai/"),),
    ),
    "openai_image": Guide(
        "文章から静止画像を作り、ズーム効果を付けた映像素材にします。動画そのものをAI生成する方式ではありません。",
        "画像生成APIのキー、Base URL、対応モデルIDを素材設定へ入力します。OpenAIを使う場合、Codexへのログインとは別のAPI設定が必要です。",
        (("OpenAI APIキー", "https://platform.openai.com/api-keys"),
         ("画像生成の公式ガイド", "https://developers.openai.com/api/docs/guides/image-generation")),
    ),
    "local": Guide(
        "自分の動画や画像をそのまま素材に使います。外部の素材サービスは不要です。",
        "下の欄でファイルをアップロードしてください。画像は縦横とも480px以上の元画像を推奨します。",
    ),
}
VIDEO_NAMES = {
    "pexels": "Pexels", "pixabay": "Pixabay", "coverr": "Coverr",
    "metaso_minimax": "METASO MiniMax H3", "ofox": "OfoxAI",
    "loomloom": "勝算雲", "volcengine_seedance": "火山方舟 Seedance",
    "wavespeed": "WaveSpeedAI", "muapi": "MuAPI",
    "openai_image": "OpenAI互換の画像生成", "local": "ローカル素材",
}


TTS_CAPABILITIES = {
    "azure-tts-v1": "Edge TTSの既定音声でナレーションを作ります。APIキーの設定は不要です。",
    "azure-tts-v2": "Azure Speechの音声でナレーションを作ります。リージョンとAPIキーが必要です。",
    "siliconflow": "SiliconFlowの音声モデルを使います。APIキーが必要です。",
    "gemini-tts": "Geminiの音声モデルを使います。話し方は自然言語の指示で調整します。",
    "mimo-tts": "Xiaomi MiMoの音声モデルを使います。APIキーが必要です。",
    "minimax-tts": "MiniMaxの音声モデルを使います。キーとサービス地域を揃えてください。",
    "elevenlabs": "ElevenLabsの音声とモデルを選んでナレーションを作ります。",
    "chatterbox": "Macなどで動かすChatterbox互換サーバーの音声を使います。",
    "kokoro": "Macなどで動かすKokoro互換サーバーの音声を使います。",
    "fish_audio": "Fish Audioの音声モデルを使います。",
    "voxcpm": "ModelBestのVoxCPMで音声を作ります。参照音声による声の再現にも対応します。",
}


SECTION_INTROS = {
    "script": (
        "最初に必要：題材か台本のどちらか一方。題材だけなら文章AIが台本を作ります。"
        "自分で台本を入力することもできます。細かな指示やモデル変更は後から調整できます。"
    ),
    "video": (
        "最初に必要：映像素材を1種類選ぶこと。自分の画像・動画ならアップロードだけで使えます。"
        "既存動画の検索サービスは選んだサービスのキー、新規AI素材は選んだサービスの設定や料金確認が必要です。"
    ),
    "audio": (
        "声とBGMを変えると、聞こえ方と雰囲気が変わります。既定のEdge TTSはキー不要。"
        "BGMは「なし」も選べます。別の音声・音楽サービスを使うときだけ接続を設定してください。"
    ),
    "subtitle": (
        "字幕は読みやすさを調整するための設定です。最初は既定のままで始められます。"
        "文字の形・位置・表示方法を変えたいときだけ調整してください。"
    ),
}


def render_section_intro(section: str, language: str) -> None:
    if language != "ja":
        return
    import streamlit as st

    st.caption(SECTION_INTROS[section])


def llm_guide(provider, endpoint=None) -> Guide:
    """Use the installed provider registry as the source for setup links."""
    if provider.provider_id == "codex_app_server":
        return Guide(
            "台本、素材検索語、投稿文案をMac miniのCodexで作ります。モデル欄を空にするとCodex側の既定モデルを使います。",
            "Mac miniで `codex login` を一度実行します。画像・動画素材や音声用のAPIキーは別設定です。",
            (("Codex app serverの公式説明", "https://learn.chatgpt.com/docs/app-server"),),
        )
    if provider.provider_id == "ollama":
        return Guide(
            "Macで動くローカルモデルで台本、素材検索語、投稿文案を作ります。",
            "Ollamaを起動し、使うモデルを取得してからモデル名と接続先を設定します。",
            (("Ollamaを入手", "https://ollama.com/download"),),
        )
    if provider.provider_id == "claude_code":
        return Guide(
            "台本、素材検索語、投稿文案をMacのClaude Codeで作ります。モデル欄が空ならCLIの既定モデルを使います。",
            "MacにClaude Codeを入れて `claude` でログインします。Claudeの利用条件と利用枠が適用されます。",
            (("Claude Codeの導入方法", "https://code.claude.com/docs/en/overview"),),
        )
    if provider.provider_id == "litellm":
        return Guide(
            "LiteLLM経由で選んだ文章モデルを使い、台本、素材検索語、投稿文案を作ります。",
            "利用するモデルと提供元を先に設定し、その提供元の認証情報を用意します。モデル名は `provider/model` 形式です。",
            (("LiteLLMの対応サービス", "https://docs.litellm.ai/docs/providers"),),
        )
    if provider.provider_id == "kimi_code":
        url = endpoint.api_key_url if endpoint else "https://www.kimi.ai/code"
        return Guide(
            "Kimi Codeのモデルで台本、素材検索語、投稿文案を作ります。",
            "利用する地域のKimi Codeプランを確認し、この画面の「Kimiでサインイン」から認証します。従量課金APIキーとは別です。",
            (("Kimi Code", url),),
        )

    api_url = (
        endpoint.api_key_url
        if endpoint else provider.effective_api_key_url(prefer_international=True)
    )
    docs_url = (
        endpoint.model_docs_url
        if endpoint and endpoint.model_docs_url
        else provider.effective_model_docs_url(prefer_international=True)
    )
    links = []
    if api_url:
        links.append(("サービスの設定・キー取得", api_url))
    if docs_url and docs_url != api_url:
        links.append(("モデル一覧・公式説明", docs_url))
    if provider.requires_api_key:
        setup = "サービス側でAPIキーを取得し、左の欄に入力します。モデルIDはサービスの説明にある正確な値を使ってください。"
    else:
        setup = "サービス側で利用登録またはログインを済ませ、左の接続設定を確認してください。"
    return Guide(
        "選んだ文章モデルで台本、素材検索語、投稿文案を作ります。モデルごとに品質・速度・利用条件が異なります。",
        setup,
        tuple(links),
    )


def _render_guide(guide: Guide, *, heading: str) -> None:
    import streamlit as st

    lines = [f"**{heading}**", guide.capability, f"**この選択を使う場合の準備**：{guide.setup}"]
    if guide.links:
        lines.append("　·　".join(f"[{label}]({url})" for label, url in guide.links))
    st.info("\n\n".join(lines))


def render_video_guide(source: str, language: str) -> None:
    if language == "ja" and source in VIDEO_GUIDES:
        _render_guide(VIDEO_GUIDES[source], heading="この映像素材を選ぶと何が変わる？")


def render_material_directory(language: str) -> None:
    if language != "ja":
        return
    import streamlit as st

    with st.expander("後から試せる映像素材サービス", expanded=False):
        st.caption("一覧のサービスを全部設定する必要はありません。使う素材サービスを選んだときだけ、そのキーや料金を確認します。")
        for source, guide in VIDEO_GUIDES.items():
            if source == "local":
                continue
            link = (
                f" · [{guide.links[0][0]}]({guide.links[0][1]})"
                if guide.links else ""
            )
            st.markdown(f"**{VIDEO_NAMES[source]}**：{guide.capability}{link}")


def render_llm_guide(provider, endpoint, language: str) -> None:
    if language == "ja":
        _render_guide(llm_guide(provider, endpoint), heading="文章モデルを変えると何が変わる？")


def render_tts_guide(server: str, existing_tip: str, language: str) -> None:
    import streamlit as st

    if language == "ja" and server in TTS_CAPABILITIES:
        lines = [f"**この声を選ぶと何が変わる？**\n\n{TTS_CAPABILITIES[server]}"]
        if existing_tip:
            lines.append(f"**この声を使う場合の準備**：{existing_tip}")
        st.info("\n\n".join(lines))
    elif existing_tip:
        st.info(existing_tip)
