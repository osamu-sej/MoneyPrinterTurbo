"""Seed MoneyPrinterTurbo's config.toml from environment variables at container start.

API keys live in the hosting platform's environment settings, not in this repo, so they
survive restarts of a container whose disk is ephemeral.
"""

import os

from app.config import config  # creates $MPT_HOME/config.toml from the bundled example


def env(name):
    return os.environ.get(name, "").strip()


provider = env("LLM_PROVIDER")
if provider:
    config.app["llm_provider"] = provider
provider = config.app.get("llm_provider", "")
for name, suffix in (("LLM_API_KEY", "api_key"), ("LLM_MODEL", "model_name"), ("LLM_BASE_URL", "base_url")):
    if env(name):
        config.app[f"{provider}_{suffix}"] = env(name)

for name, key in (("PEXELS_API_KEY", "pexels_api_keys"), ("PIXABAY_API_KEY", "pixabay_api_keys")):
    if env(name):
        config.app[key] = [k.strip() for k in env(name).split(",") if k.strip()]

# Japanese defaults: Edge TTS voice and a font that has kana glyphs
config.ui["voice_name"] = env("MPT_VOICE_NAME") or "ja-JP-NanamiNeural-Female"
font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
if os.path.isfile(font):
    link = os.path.join(config.root_dir, "resource", "fonts", os.path.basename(font))
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if not os.path.lexists(link):
        os.symlink(font, link)
    config.ui["font_name"] = os.path.basename(font)

config.save_config()
print(
    f"config seeded: llm_provider={provider}, pexels_keys={len(config.app.get('pexels_api_keys', []))}, "
    f"voice={config.ui['voice_name']}, font={config.ui.get('font_name')}"
)
