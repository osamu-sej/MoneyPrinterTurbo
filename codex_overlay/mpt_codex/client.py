"""A bounded, text-only client for the Codex app-server JSONL protocol."""

import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time


class CodexError(RuntimeError):
    pass


def _child_env():
    # The model receives untrusted video subjects. Keep the child away from
    # credentials used by the video renderer and other installed providers.
    names = (
        "PATH", "HOME", "USER", "USERNAME", "TMPDIR", "TEMP", "TMP",
        "LANG", "LC_ALL", "LC_CTYPE", "SYSTEMROOT", "WINDIR", "APPDATA",
        "LOCALAPPDATA", "CODEX_HOME", "SSL_CERT_FILE", "CODEX_CA_CERTIFICATE",
    )
    return {name: os.environ[name] for name in names if name in os.environ}


def _read_messages(stream, messages):
    try:
        for line in stream:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                messages.put(CodexError("Codex app-server returned invalid JSON"))
    finally:
        messages.put(CodexError("Codex app-server closed its output"))


def generate(prompt: str, *, model: str = "", timeout: float = 300.0) -> str:
    if not prompt.strip():
        raise CodexError("empty prompt")
    executable = shutil.which(os.environ.get("MPT_CODEX_CLI", "codex"))
    if not executable:
        raise CodexError("Codex CLI is not installed or not on PATH")
    deadline = time.monotonic() + timeout
    messages = queue.Queue()
    with tempfile.TemporaryDirectory(prefix="mpt-codex-") as work_dir:
        proc = subprocess.Popen(
            [executable, "app-server", "--listen", "stdio://"],
            cwd=work_dir,
            env=_child_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        threading.Thread(
            target=_read_messages, args=(proc.stdout, messages), daemon=True
        ).start()

        def send(method, params=None, request_id=None):
            message = {"method": method, "params": params or {}}
            if request_id is not None:
                message["id"] = request_id
            try:
                proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
                proc.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                raise CodexError("Codex app-server stopped") from exc

        def receive():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CodexError("Codex app-server timed out")
            try:
                message = messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise CodexError("Codex app-server timed out") from exc
            if isinstance(message, Exception):
                raise message
            if "error" in message:
                raise CodexError(str(message["error"].get("message", "request failed")))
            if "id" in message and "result" not in message:
                raise CodexError("Codex app-server requested an unsupported action")
            return message

        def response(request_id):
            while True:
                message = receive()
                if message.get("id") == request_id:
                    return message["result"]
                pending.append(message)

        pending = []
        try:
            send(
                "initialize",
                {
                    "clientInfo": {
                        "name": "moneyprinterturbo_codex",
                        "title": "MoneyPrinterTurbo Codex",
                        "version": "0.1.0",
                    }
                },
                1,
            )
            response(1)
            send("initialized")
            send("model/list", {}, 2)
            available = response(2).get("data", [])
            if not model.strip():
                selected = next(
                    (item for item in available if item.get("isDefault")),
                    available[0] if available else {},
                )
                model = selected.get("model", "")
            if not model:
                raise CodexError("Codex app-server has no available model")
            thread_params = {
                "cwd": work_dir,
                "approvalPolicy": "never",
                "sandbox": "read-only",
                "ephemeral": True,
                "baseInstructions": (
                    "You write plain text for a short-video production app. "
                    "Follow the user's requested format exactly. "
                    "Do not use tools, inspect files, or add commentary."
                ),
            }
            thread_params["model"] = model.strip()
            send("thread/start", thread_params, 3)
            thread_id = response(3)["thread"]["id"]
            send(
                "turn/start",
                {"threadId": thread_id, "input": [{"type": "text", "text": prompt}]},
                4,
            )
            response(4)
            deltas = []
            completed_text = ""
            while True:
                message = pending.pop(0) if pending else receive()
                method = message.get("method")
                params = message.get("params") or {}
                if method == "item/agentMessage/delta":
                    deltas.append(params.get("delta", ""))
                elif method == "item/completed":
                    item = params.get("item") or {}
                    if item.get("type") == "agentMessage" and item.get("text"):
                        completed_text = item["text"]
                elif method == "turn/completed":
                    turn = params.get("turn") or {}
                    if turn.get("status") != "completed":
                        error = turn.get("error") or {}
                        raise CodexError(error.get("message") or "Codex turn did not complete")
                    text = (completed_text or "".join(deltas)).strip()
                    if not text:
                        raise CodexError("Codex returned empty text")
                    return text
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            proc.stdin.close()
            proc.stdout.close()
