from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from logging_utils import write_json, write_text


DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")


class OllamaClient:
    def __init__(self, host: str = DEFAULT_HOST) -> None:
        self.host = host.rstrip("/")

    def list_models(self) -> dict[str, Any]:
        return self._get_json("/api/tags")

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        run_dir: Path,
        options: dict[str, Any] | None = None,
        system: str | None = None,
        keep_alive: str | None = None,
        think: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options
        if system:
            payload["system"] = system
        if keep_alive:
            payload["keep_alive"] = keep_alive
        if think is not None:
            payload["think"] = think

        request_path = run_dir / "request.json"
        prompt_path = run_dir / "prompt.txt"
        write_json(request_path, payload)
        write_text(prompt_path, prompt)

        start = time.time()
        try:
            response = self._post_json("/api/generate", payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            write_text(run_dir / "error.txt", body)
            raise RuntimeError(f"Ollama HTTP error {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            write_text(run_dir / "error.txt", str(exc))
            raise RuntimeError(f"Could not reach Ollama at {self.host}") from exc
        except Exception as exc:  # pragma: no cover
            write_text(run_dir / "error.txt", repr(exc))
            raise

        elapsed = time.time() - start
        response["client_elapsed_seconds"] = elapsed
        write_json(run_dir / "response.json", response)
        write_text(run_dir / "response_text.txt", response.get("response", ""))
        if "thinking" in response:
            write_text(run_dir / "thinking_text.txt", response.get("thinking", ""))
        return response

    def _get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(f"{self.host}{path}", method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
        return json.loads(body)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            response_body = response.read().decode("utf-8")
        return json.loads(response_body)
