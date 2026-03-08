# Final Results and Evidence

## Evaluation Scope
This project was evaluated in two ways:
- Standard run with base dataset size (15 examples)
- Extended run for evidence requirements using `EVAL_SAMPLE_SIZE=20`

The extended run does not modify `src/dataset.py`; it cycles existing examples to produce 20 evaluated samples.

## Commands Executed

### Baseline prompt (v1)
```bash
EVAL_SAMPLE_SIZE=20 PROMPT_FILE=prompts/bug_to_user_story_v1.yml python src/evaluate.py
```

### Optimized prompt (v2)
```bash
EVAL_SAMPLE_SIZE=20 PROMPT_FILE=prompts/bug_to_user_story_v2.yml python src/evaluate.py
```

### Validation tests
```bash
pytest tests/test_prompts.py -v
```

## Metrics - 20 Sample Evidence

| Metric | v1 (bad) | v2 (optimized) |
|---|---:|---:|
| Tone Score | 0.7300 | 0.9150 |
| Acceptance Criteria Score | 0.3000 | 0.9533 |
| User Story Format Score | 0.0000 | 1.0000 |
| Completeness Score | 0.1375 | 1.0000 |
| Average | 0.2919 | 0.9671 |

Status:
- v1: FAILED
- v2: APPROVED (all 4 metrics >= 0.9)

## Metrics - 15 Sample Standard Run

| Metric | v1 (bad) | v2 (optimized) |
|---|---:|---:|
| Tone Score | 0.7367 | 0.9133 |
| Acceptance Criteria Score | 0.3000 | 0.9689 |
| User Story Format Score | 0.0000 | 1.0000 |
| Completeness Score | 0.1500 | 1.0000 |
| Average | 0.2967 | 0.9706 |

Status:
- v1: FAILED
- v2: APPROVED (all 4 metrics >= 0.9)

## LangSmith Links
- Source prompt (v1): `leonanluppi/bug_to_user_story_v1`
- Published prompt (v2): `initialhandle/bug_to_user_story_v2`
- Public prompt URL: https://smith.langchain.com/prompts/bug_to_user_story_v2/963384b2

## Artifacts
- Per-example outputs: `evaluation_results.json`
- Prompt files:
  - `prompts/bug_to_user_story_v1.yml`
  - `prompts/bug_to_user_story_v2.yml`
- Test suite: `tests/test_prompts.py`

## Notes for Submission
- Include screenshots from LangSmith dashboard showing:
  - v1 low-score evaluation
  - v2 approved evaluation
  - traces for at least 3 examples

## Latest End-to-End Run (2026-03-08)

This section records the most recent full run from start to finish.

### Step 1: Pull baseline prompt
Command:
```bash
python src/pull_prompts.py
```
Observed output:
- Pulled from LangSmith Hub: `leonanluppi/bug_to_user_story_v1`
- Saved files:
  - `prompts/bug_to_user_story_v1.yml`
  - `prompts/raw_prompts.yml`

### Step 2: Evaluate baseline v1
Command:
```bash
PROMPT_FILE=prompts/bug_to_user_story_v1.yml python src/evaluate.py
```
Observed output:
- Samples: `15`
- Tone Score: `0.7367`
- Acceptance Criteria Score: `0.3000`
- User Story Format Score: `0.0000`
- Completeness Score: `0.1500`
- Average: `0.2967`
- Status: `FAILED`

### Step 3: Push optimized v2
Command:
```bash
python src/push_prompts.py
```
Observed output:
- Target: `initialhandle/bug_to_user_story_v2`
- Commit URL: `https://smith.langchain.com/prompts/bug_to_user_story_v2/963384b2`
- Techniques metadata printed: `role-prompting, few-shot-learning, skeleton-of-thought`
- Tags metadata printed: `optimized, prompt-engineering, bug-to-user-story`

### Step 4: Evaluate optimized v2
Command:
```bash
PROMPT_FILE=prompts/bug_to_user_story_v2.yml python src/evaluate.py
```
Observed output:
- Samples: `15`
- Tone Score: `0.9133`
- Acceptance Criteria Score: `0.9689`
- User Story Format Score: `1.0000`
- Completeness Score: `1.0000`
- Average: `0.9706`
- Status: `APPROVED`

### Step 5: Validate tests
Command:
```bash
pytest tests/test_prompts.py -q
```
Observed output:
- `6 passed`
