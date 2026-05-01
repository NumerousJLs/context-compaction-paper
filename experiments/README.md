# Experiments Runtime

This folder contains the local runtime for:

- starting and checking Ollama
- pulling models
- running smoke tests
- saving debug logs
- saving experiment outputs

## Layout

- `bin/`: shell entrypoints
- `config/`: model/runtime config examples
- `context_compaction/`: Python helpers
- `logs/`: server logs and pull logs
- `outputs/`: per-run saved outputs

## Main commands

Start or verify Ollama:

```bash
./experiments/bin/ensure_ollama.sh
```

Pull a model:

```bash
./experiments/bin/pull_model.sh qwen3:8b
```

Run a smoke test:

```bash
./experiments/bin/smoke_test.sh llama3:latest
```

## Logging behavior

- server logs go to `experiments/logs/ollama_server.log`
- pull logs go to timestamped files in `experiments/logs/`
- smoke tests and later experiment runs create a timestamped directory in `experiments/outputs/`

## Notes

- The main experiment code should save every run with:
  - request metadata
  - model name
  - prompt input
  - raw response
  - parsed response
  - runtime info
  - any errors
- This makes failed runs debuggable without rerunning everything.
