# Hi
# Prompt Engineering Challenge - LangChain + LangSmith

## Overview
This project pulls low-quality prompts from LangSmith Prompt Hub, optimizes them with advanced prompt engineering techniques, pushes them back to LangSmith, and evaluates quality with custom metrics.

This implementation uses an **Ollama-first strategy**:
- Try local Ollama model first.
- If Ollama is unavailable, automatically fallback to configured cloud provider (OpenAI or Gemini).

## Project Structure

```
desafio-prompt-engineer/
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml
│   ├── bug_to_user_story_v2.yml
│   └── raw_prompts.yml
├── src/
│   ├── pull_prompts.py
│   ├── push_prompts.py
│   ├── evaluate.py
│   ├── metrics.py
│   ├── dataset.py
│   └── utils.py
└── tests/
    └── test_prompts.py
```

## Prerequisites
- Python 3.9+
- LangSmith API key
- One of the following:
  - Ollama running locally with a pulled model (recommended)
  - OpenAI API key
  - Google API key (Gemini)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then fill `.env` values.

## Model Resolution Strategy (Fixed Sequence)
`src/utils.py` resolves model clients in this strict order:
1. Ollama (`OLLAMA_BASE_URL` + `OLLAMA_MODEL`)
2. OpenAI (`OPENAI_API_KEY`, `OPENAI_MODEL` / `OPENAI_EVAL_MODEL`)
3. Gemini (`GOOGLE_API_KEY`, `GEMINI_MODEL` / `GEMINI_EVAL_MODEL`)

If none is available, execution fails with a clear message telling the user that no model provider is available.

This applies to both generation (`response`) and evaluator (`evaluation`) models.

## Evaluation Modes
Set `EVAL_MODE` in `.env`:
- `heuristic`: deterministic local metrics only
- `llm`: LLM judge metrics only
- `hybrid` (default): average of heuristic + LLM judge scores

If LLM judge output is invalid JSON, evaluation safely falls back to heuristic score for that sample.

## How to Execute

### 1. Pull baseline prompt (v1) from LangSmith
```bash
python src/pull_prompts.py
```

This creates:
- `prompts/bug_to_user_story_v1.yml`
- `prompts/raw_prompts.yml`

### 2. Evaluate baseline v1 (expected to FAIL)
Run evaluation explicitly with v1 to show negative baseline results:

```bash
PROMPT_FILE=prompts/bug_to_user_story_v1.yml python src/evaluate.py
```

Expected outcome:
- Low scores (below `0.9`)
- Status: `FAILED`

### 3. Use the enhanced v2 prompt
The optimized prompt is already in:
- `prompts/bug_to_user_story_v2.yml`

If needed, iterate by editing this file and re-running steps 4 to 6.

### 4. Run validation tests for v2
```bash
pytest tests/test_prompts.py
```

Expected outcome:
- `6 passed`

### 5. Push optimized prompt (v2) to LangSmith
```bash
python src/push_prompts.py
```

### 6. Evaluate optimized v2 (expected to PASS)
Run evaluation explicitly with v2:

```bash
PROMPT_FILE=prompts/bug_to_user_story_v2.yml python src/evaluate.py
```

Expected outcome:
- All four metrics >= `0.9`
- Status: `APPROVED`

## Applied Techniques (Phase 2)
The optimized prompt (`prompts/bug_to_user_story_v2.yml`) applies these advanced techniques:

1. Role Prompting
- Why: sets a stable persona and domain context for consistent output quality.
- How applied: system prompt starts with "You are a Senior Product Manager..." and enforces behavior rules.

2. Few-shot Learning
- Why: gives the model concrete examples of the exact output quality and format expected.
- How applied: two complete input/output examples are included (password reset tokens and mobile Safari checkout).

3. Skeleton of Thought
- Why: improves reasoning quality without exposing chain-of-thought details in the final output.
- How applied: explicit step structure in system prompt:
  - identify persona
  - define behavior/value
  - produce concise user story
  - produce measurable acceptance criteria

## Final Results
Detailed results and evidence are documented in:

- `RESULTS.md`

This includes:
- 20-sample evaluation evidence (`EVAL_SAMPLE_SIZE=20`) for v1 and v2
- Standard 15-sample comparison
- LangSmith links
- Reproduction commands
- Submission checklist items for screenshots/traces

## Spec Compliance Notes
- Required folders/files are present according to the challenge structure.
- `pull_prompts.py` saves pulled prompt to both:
  - `prompts/bug_to_user_story_v1.yml`
  - `prompts/raw_prompts.yml`
- Both command names are supported:
  - `python src/pull_prompts.py` and `python src/pull_prompt.py`
  - `python src/push_prompts.py` and `python src/push_prompt.py`
- Required pytest validations are implemented in `tests/test_prompts.py`.

## Notes
- Keep evaluation dataset unchanged.
- Perform 3-5 optimization iterations until all required metrics are >= 0.9.
- Publish final v2 prompt publicly on LangSmith Prompt Hub.
