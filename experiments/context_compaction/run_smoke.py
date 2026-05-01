from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from logging_utils import create_run_dir, write_json  # noqa: E402
from ollama_client import OllamaClient  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal Ollama smoke test.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    run_dir = create_run_dir("smoke")
    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"
    client = OllamaClient()

    metadata = {
        "script": "run_smoke.py",
        "model": args.model,
        "run_dir": str(run_dir.relative_to(outputs_dir)),
    }
    write_json(run_dir / "metadata.json", metadata)

    response = client.generate(
        args.model,
        args.prompt,
        run_dir=run_dir,
        options={"temperature": 0},
    )

    print(f"Run directory: {run_dir}")
    print(response.get("response", "").strip())


if __name__ == "__main__":
    main()
