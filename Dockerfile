# MoneyPrinterTurbo (official PyPI package mpt) WebUI for Render, behind an access-key gate.
# Needs about 1GB of RAM while rendering a video (measured peak 680MB), so use a 2GB plan.
FROM caddy:2.8 AS caddy

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPT_HOME=/data \
    XDG_DATA_HOME=/tmp/caddy \
    XDG_CONFIG_HOME=/tmp/caddy

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

RUN pip install mpt==1.3.8

COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
COPY deploy/ /app/deploy/

CMD ["bash", "/app/deploy/entrypoint.sh"]
