"""Register Codex as an MPT provider without modifying the installed wheel."""

import os

from .client import CodexError, generate


def install():
    from app import __version__

    if __version__ != "1.3.8":
        raise RuntimeError("Codex integration requires mpt==1.3.8")

    from app.models import llm_provider

    provider = llm_provider.LLMProviderSpec(
        "codex_app_server",
        "Codex app server (ChatGPT login)",
        adapter="codex_app_server",
        requires_api_key=False,
        show_api_key=False,
        requires_base_url=False,
        show_base_url=False,
        requires_model_name=False,
    )
    llm_provider.LLM_PROVIDER_REGISTRY += (provider,)
    llm_provider.LLM_PROVIDERS[provider.provider_id] = provider

    from app.config import config
    from app.services import llm

    original = llm._generate_response

    def codex_response(prompt, app_config=None, request_timeout=None, max_retries=None):
        runtime_config = app_config if app_config is not None else config.app
        if runtime_config.get("llm_provider") != provider.provider_id:
            return original(prompt, app_config, request_timeout, max_retries)
        model = str(runtime_config.get("codex_app_server_model_name") or "")
        try:
            return generate(
                prompt,
                model=model,
                timeout=float(request_timeout or os.environ.get("MPT_CODEX_TIMEOUT", 300)),
            )
        except (CodexError, OSError, ValueError) as exc:
            return f"Error: Codex app server: {exc}"

    llm._generate_response = codex_response
