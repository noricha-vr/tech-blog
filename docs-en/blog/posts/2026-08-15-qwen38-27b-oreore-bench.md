---
date:
  created: 2026-08-15
slug: qwen38-27b-oreore-bench
authors:
  - noricha
tags:
  - AI
  - LLM
categories:
  - AI
---

# A 27B Local Model Got 189 of 191 Fields Right — and Missed the Same One as Gemma 4

I benchmarked Qwen3.8-27B, released by Alibaba under Apache 2.0, across all nine themes of my personal benchmark. On structured output it is the best locally runnable model I have measured, but one-shot HTML generation exposes a different weakness.

<!-- more -->

## What I measured

[OreOre-Bench](https://oreore-bench.pages.dev) sends the same frozen prompt to each model exactly once and puts the artifacts side by side. Nothing is hand-fixed afterward.

| Setting | Value |
|---|---|
| Model | `Qwen/Qwen3.8-27B` (released 2026-08-05, Apache 2.0) |
| Quantization | unsloth GGUF Q8_0 (29GB) |
| Runtime | Ollama 0.30.6 / Mac Studio M3 Ultra 512GB |
| Sampling | temperature 0.3, default top_p, max_tokens 65,000 (same for every model) |
| Themes | 7 HTML generation + 2 structured JSON |

It is a 27B dense model that repeats a block of three Gated DeltaNet layers plus one Gated Attention layer sixteen times, with a native 262K context. Thinking mode is on by default.

## Structured output is clearly strong

The json-ladder theme asks the model to extract progressively harder JSON from the same short story — from a simple title lookup at L1 up to L6, which requires indexing the opening phrase of every paragraph verbatim.

| Level | Fields | Matched | Accuracy |
|---|---|---|---|
| L1–L4 | 41 | 41 | 100% |
| L5 | 54 | 53 | 98% |
| L6 | 96 | 95 | 99% |
| **Total** | **191** | **189** | 99.5% average |

189 of 191 fields matched. That is the best result I have from any locally runnable model, edging out the previous leader Gemma 4 31B at 99%.

It is not a perfect score, though. Here are the two misses:

```text
L5  characters[0].relations   got: 1        expected: 0
L6  sections[3].paragraph_openings[2]
      got: "> 千鶴へ"   expected: "千鶴へ"
```

The L6 miss is a letter quoted inside the prose: the model failed to strip the leading `>` quote marker from the opening line. That is exactly the same field Gemma 4 31B misses on this theme. Model scale and generation change, but the judgment call of "how much of the original formatting should I strip" seems to break at the same place.

On the PR triage theme (classify ten pull requests as merge / fix / hold / close), it hit 90% agreement with the answer key, above the 85% of all three Gemma 4 models. Notably, that theme instructs the model to return JSON only — and Qwen3.8 obeyed even while producing a long thinking block. Claude Opus 4.8 breaks that same instruction by prepending prose.

## HTML generation leaks preambles

One-shot HTML tells a different story.

**Six of the seven HTML themes had a preamble or a code fence at the top of the artifact.**

```text
hasami-shogi  "A complete implementation in a single `index.html`. The rule set..."
lp-fable5     "A picture-book style announcement page for Fable 5, with watercolor SVG..."
lp-nishibi    "# NISHIBI — frozen prompt implementation"
othello       "A complete Othello in a single `index.html`. Green felt board..."
phoenix-lp    ```html
suminagashi   "Full-screen ink swirling and dissolving on washi paper..."
roguelike     (clean — starts with <!DOCTYPE html>)
```

Trailing implementation notes show up too. Browsers are forgiving enough that the pages still render, but the instruction was "output a single HTML file," and this does not satisfy it.

What makes it interesting is that both structured JSON themes were completely clean. The model respects the format strictly when the output is JSON, and wants to add commentary when the output is HTML.

The content quality itself is high. The Fable 5 landing page came with watercolor SVG illustrations, a serif display typeface, and scroll-driven animation. The Othello implementation had legal-move highlighting, 3D flip animation, and pass handling — I verified moves and CPU responses with Playwright.

Two themes failed. The roguelike has a beautifully built title screen but throws six JS errors once the game starts. Suminagashi (a WebGL fluid simulation) could not compile its fragment shader, following the pattern of every local model failing this theme so far.

## Is 18.8 tok/s fast?

Weighted average across eight themes was 18.8 tok/s.

| Theme | completion | seconds | tok/s |
|---|---|---|---|
| pr-triage | 12,004 | 616 | 19.5 |
| othello | 38,563 | 2,012 | 19.2 |
| lp-nishibi | 38,734 | 2,025 | 19.1 |
| hasami-shogi | 38,519 | 2,022 | 19.0 |
| lp-fable5 | 55,360 | 2,968 | 18.7 |
| suminagashi | 50,516 | 2,723 | 18.5 |
| phoenix-lp | 65,000 | 3,533 | 18.4 |

The variance is remarkably small — 18.4 to 19.5. Even the run that emitted 65,000 tokens held 18.4, so throughput barely degrades as the KV cache grows.

What actually mattered was not tok/s but **total tokens per request**. Thinking is on by default and runs long, so a single HTML page takes 32 to 59 minutes. Across nine themes the completion total was 370,866 tokens.

The phoenix-lp run hit the 65,000 token ceiling and its trailing JavaScript is cut off mid-comment. The canvas rendering and scroll animation still worked, so the smoke test passed anyway — a case where "the test passes" and "the output is complete" diverge.

Practically, this speed and thinking length constrain the use case. A 30-minute response is rough for interactive work, but for batch extraction of structured data, 189 out of 191 is compelling.

## I had to redo the measurement twice

It did not go smoothly.

### The MLX server dies after ten minutes

I first converted the model to MLX 8bit myself and served it with `mlx_lm.server`. Roughly ten minutes and ten thousand tokens into generation, the generation thread dies:

```text
RuntimeError: [metal::malloc] Resource limit (499000) exceeded.
```

I read `499000` as "a 499GB memory ceiling" and started hunting for memory exhaustion. But measurements showed active memory flat at 29GB with zero swap growth — plenty of headroom. The hypothesis did not match the observation.

The limit is **not a byte count; it is the number of Metal buffers**. The MLX allocator checks `num_resources_ >= resource_limit_`. When the order of magnitude disagrees with your measurements, question the unit.

The decisive step was **comparing the server path against direct generation under identical conditions**:

```python
# Same model, same prompt, same max_tokens — straight through
for _ in stream_generate(model, tokenizer, text, max_tokens=65000):
    ...
```

Direct `stream_generate` sailed through 13,400 tokens in 644 seconds, well past where the server died. That pinned the problem to `mlx_lm.server`'s generation path rather than the model or the token count.

The nasty part: **the process stays alive while only the generation thread dies**. From the client it looks like a hang, and a `pgrep` liveness check detects nothing. Server-log `Exception` lines belong in the monitoring conditions.

I switched to llama.cpp (Ollama with an equivalent Q8_0 GGUF) and completed all nine themes. Keeping the quantization at 8bit preserves the comparison. MLX's direct path was 21 tok/s, about 12% faster, so MLX would have been the better choice had the server held up.

### The verification script failed a correct implementation

The hasami-shogi smoke test reported "10 pawns, 10 promoted pawns" where the initial position should be nine of each.

The screenshot showed a correct nine-per-side board. The script was counting the single-character badges in the scoreboard on the right, because it counted every leaf element on the page whose text was one of the two piece characters.

I changed it to infer the board grid from piece coordinates and count only inside that rectangle — and review found a worse trap in that fix.

**If you take "the longest run of evenly spaced columns" as the board, a model that places pieces wrong also shifts the inferred board, so the extra pieces get reclassified as off-board and the run passes.** I reproduced it: a ten-column board holding ten pieces was counted as 9/9 and passed.

Deriving the pass criteria from the artifact under test makes the criteria looser exactly when the input is broken. The final version decides column membership by whether pieces sit on a detected board row, not by x-distance, and fails outright when the inferred column count is not nine.

## Takeaways

- Structured JSON extraction hit 189 of 191 fields, the best I have measured locally
- It still misses where Gemma 4 misses: deciding how much original formatting to strip
- Six of seven HTML themes leaked preambles, while both JSON themes were clean
- 18.8 tok/s is stable, but long thinking means 30 to 59 minutes per page
- When an error's order of magnitude disagrees with your measurements, question the unit
- Deriving pass criteria from the artifact under test loosens them exactly when the input is broken

All nine artifacts and their generation conditions are published at [OreOre-Bench](https://oreore-bench.pages.dev).
