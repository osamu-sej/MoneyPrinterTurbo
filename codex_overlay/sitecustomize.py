"""Load the Codex provider before MoneyPrinterTurbo imports its provider registry."""

import os

if os.environ.get("MPT_CODEX_APP_SERVER") == "1":
    from mpt_codex.integration import install

    install()
