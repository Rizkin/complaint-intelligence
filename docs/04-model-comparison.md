# Local model comparison: decision models vs the chat baseline

Same 600 held-out complaints (2026-05), same metrics as `docs/03-classifier-baseline.md`. Hardware: RTX 3050 Laptop 4 GB VRAM, 16 GB RAM
(only 0.3 to 3.5 GB free during these runs). Everything is local and costs $0.

## What changed in Ollama

Ollama 0.40 added **decision models**: a `/v1/systemone` endpoint where you send `state` (the text) and typed `questions`
(`choice`, `noul` yes/no, `score`) and get back a **probability for every option** in one forward pass, with no text generation.
Upgraded Ollama 0.35.0 -> 0.40.3 (existing models kept).

## Which models can run here

| Model | Size | Runs on this laptop? |
|-------|------|----------------------|
| `tev1:0.8b-q8_0` (Together AI, Qwen3.5 fine-tune) | 0.8 GB | Yes, 100% GPU, 893 MB |
| `tev1:4b-q4_K_M` | 2.7 GB (3.5 GB loaded) | Partly: 67% GPU / 33% CPU, free RAM fell to 0.3 GB |
| `laya` (421M ModernBERT) | 0.85 GB | No: "requires MLX support, MLX runtime is not available" |
| `strands-decider`, `kev` | 1.3 to 6.7 GB | No: published as Apple-silicon MLX builds (not tried) |
| `nimble`, `nimble-v3`, `clef-flash` (9B), `clef` (27B) | 5 GB+ | Not tried: far above 4 GB VRAM and free RAM |

## Results

| System | Product macro-F1 | Issue macro-F1 | Issue accuracy | Speed (median s/item) |
|--------|-----------------:|---------------:|---------------:|----------------------:|
| qwen3.5:2b chat, zero-shot (baseline v0) | 0.861 | 0.122 | 0.143 | 1.55 (avg) |
| tev1 0.8B decision | 0.792 | 0.129 | 0.127 | 0.57 |
| tev1 0.8B + product-constrained issue | 0.792 | 0.223 | 0.200 | 0.57 |
| tev1 4B decision | 0.905 | 0.214 | 0.280 | 1.78 |
| **tev1 4B + product-constrained issue** | **0.905** | **0.341** | **0.412** | 1.78 |
| TF-IDF + logistic regression (supervised reference) | 0.955 | 0.498 | 0.637 | CPU, trained offline |

"Product-constrained" = take the highest-probability issue among the issues valid for the predicted product (a free post-step, only possible
because decision models return the full probability vector). It fixes failure pattern 1 from the baseline (issues from the wrong product).

## Reading it

- **The decision model 4B is the best local zero-shot option**: issue macro-F1 0.341 vs 0.122 for the chat baseline (2.8x), product 0.905 vs 0.861.
- **It does not beat the supervised reference** (0.498). Consumer-chosen issues follow conventions that training data teaches and a prompt does not.
- **The 0.8B is the speed pick** (0.57 s/item, 893 MB, leaves RAM and GPU free) and is better than the baseline on issue only after the constraint; its product
  detection is worse (0.792).
- **Memory is the real limit**: the 4B spills to CPU and left 0.3 GB of free RAM, which is fine for an overnight batch but not for running next to the
  agent, Docker and a browser. Use the 0.8B or the supervised model for anything interactive.

## What decision models are actually good for here

Probabilities with confidence, in one pass, for **yes/no questions** (`noul`) and **scores**: "does the consumer report an unauthorized electronic
transaction?" (Reg E), "is there a billing error dispute?" (Reg Z), "has the consumer asked for the account to be reopened?". Those map directly to the
regulation-mapping and triage-risk work, and to the labeled 60-item golden set in Week 2. A first probe on one narrative gave 0.857 for the
unauthorized-transaction question (correct). This is a better use than the 24-way consumer-label task.

## Recommendation

1. Keep the **supervised TF-IDF-style model as the product and issue classifier** (0.955 / 0.498); it is also cheap (CPU) and fast at inference.
2. Use **tev1:0.8b-q8_0** for typed yes/no and score questions (regulation triggers, urgency), on the Cloud-side path in Week 2.
3. Use **tev1:4b-q4_K_M** only for offline batch runs when nothing else is running.
4. Next experiment: stack the decision model's 24 issue probabilities with the supervised probabilities (the vectors are saved in `data/eval/pred_tev1_*.parquet`).

## Reproduce

```bash
evals/docker_run.sh python evals/classify_decision.py --model tev1:0.8b-q8_0 --tag tev1_0.8b
evals/docker_run.sh python evals/classify_decision.py --model tev1:4b-q4_K_M --tag tev1_4b
uv run python evals/classify.py report      # all pred_*.parquet -> evals/results/
```

Run metadata: `evals/results/run_meta_tev1_0.8b.json`, `run_meta_tev1_4b.json` (600 items, 0 errors each; 351 s and 1,125 s).
