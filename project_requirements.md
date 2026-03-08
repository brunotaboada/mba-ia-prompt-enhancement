# Pull, Optimization and Evaluation of Prompts with LangChain and LangSmith

## Objective
You must deliver software capable of:

- Pulling prompts from LangSmith Prompt Hub containing low-quality prompts
- Refactoring and optimizing these prompts using advanced Prompt Engineering techniques
- Pushing optimized prompts back to LangSmith
- Evaluating quality through custom metrics (F1-Score, Clarity, Precision)
- Achieving a minimum score of 0.9 (90%) on all evaluation metrics

## CLI Example

```bash
# Execute pull of bad prompts from LangSmith
python src/pull_prompts.py

# Execute initial evaluation (bad prompts)
python src/evaluate.py

Executing prompt evaluation...
================================
Prompt: support_bot_v1a
- Helpfulness: 0.45
- Correctness: 0.52
- F1-Score: 0.48
- Clarity: 0.50
- Precision: 0.46
================================
Status: FAILED - Metrics below minimum of 0.9

# After refactoring prompts and pushing
python src/push_prompts.py

# Execute final evaluation (optimized prompts)
python src/evaluate.py

Executing prompt evaluation...
================================
Prompt: support_bot_v2_optimized
- Helpfulness: 0.94
- Correctness: 0.96
- F1-Score: 0.93
- Clarity: 0.95
- Precision: 0.92
================================
Status: APPROVED ✓ - All metrics reached minimum of 0.9
```

## Required Technologies
- **Language**: Python 3.9+
- **Framework**: LangChain
- **Evaluation Platform**: LangSmith
- **Prompt Management**: LangSmith Prompt Hub
- **Prompt Format**: YAML

## Recommended Packages

```python
from langchain import hub  # Pull and Push prompts
from langsmith import Client  # Interaction with LangSmith API
from langsmith.evaluation import evaluate  # Prompt evaluation
from langchain_openai import ChatOpenAI  # OpenAI LLM
from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini LLM
```

## OpenAI
- Create an OpenAI API Key: https://platform.openai.com/api-keys
- LLM model for responses: `gpt-4o-mini`
- LLM model for evaluation: `gpt-4o`
- Estimated cost: ~$1-5 to complete the challenge

## Gemini (free model)
- Create a Google API Key: https://aistudio.google.com/app/apikey
- LLM model for responses: `gemini-2.5-flash`
- LLM model for evaluation: `gemini-2.5-flash`
- Limit: 15 req/min, 1500 req/day

## Requirements

### 1. Pull Initial Prompt from LangSmith

The base repository already contains low-quality prompts published on LangSmith Prompt Hub. Your first task is to create code capable of pulling these prompts to your local environment.

**Tasks:**

- Configure your LangSmith credentials in the `.env` file (according to instructions in the base repository's README.md)
- Access the script `src/pull_prompts.py` that:
  - Connects to LangSmith using your credentials
  - Pulls the following prompt:
    - `leonanluppi/bug_to_user_story_v1`
  - Saves the prompts locally in `prompts/raw_prompts.yml`

### 2. Prompt Optimization

Now that you have the initial prompt, it's time to refactor it using the prompt techniques learned in the course.

**Tasks:**

- Analyze the prompt in `prompts/bug_to_user_story_v1.yml`
- Create a new file `prompts/bug_to_user_story_v2.yml` with your optimized versions
- Apply at least two of the following techniques:
  - **Few-shot Learning**: Provide clear input/output examples
  - **Chain of Thought (CoT)**: Instruct the model to "think step by step"
  - **Tree of Thought**: Explore multiple reasoning paths
  - **Skeleton of Thought**: Structure the response in clear steps
  - **ReAct**: Reasoning + Action for complex tasks
  - **Role Prompting**: Define detailed persona and context
- Document in README.md which techniques you chose and why

**Optimized prompt requirements:**

- Must contain clear and specific instructions
- Must include explicit behavior rules
- Must have input/output examples (Few-shot)
- Must include edge case handling
- Must properly use System vs User Prompt

### 3. Push and Evaluation

After refactoring the prompts, you must send them back to LangSmith Prompt Hub.

**Tasks:**

**1. Create the script `src/push_prompts.py` that:**

- Reads optimized prompts from `prompts/bug_to_user_story_v2.yml`
- Pushes to LangSmith with versioned names:
  - `{your_username}/bug_to_user_story_v2`
- Adds metadata (tags, description, techniques used)

**2. Execute the script and verify on the LangSmith dashboard that the prompts were published**

**3. Make it public**

### 4. Iteration

Expect 3-5 iterations:
- Analyze low metrics and identify problems
- Edit prompt, push and evaluate again
- Repeat until ALL metrics >= 0.9

**Approval Criteria:**
- Tone Score >= 0.9
- Acceptance Criteria Score >= 0.9
- User Story Format Score >= 0.9
- Completeness Score >= 0.9

**AVERAGE of the 4 metrics >= 0.9**

**IMPORTANT: ALL 4 metrics must be >= 0.9, not just the average!**

### 5. Validation Tests

**What you must do:** Edit the file `tests/test_prompts.py` and implement, at minimum, the 6 tests below using pytest:

- `test_prompt_has_system_prompt`: Verifies that the field exists and is not empty
- `test_prompt_has_role_definition`: Verifies that the prompt defines a persona (e.g., "You are a Product Manager")
- `test_prompt_mentions_format`: Verifies that the prompt requires Markdown format or standard User Story
- `test_prompt_has_few_shot_examples`: Verifies that the prompt contains input/output examples (Few-shot technique)
- `test_prompt_no_todos`: Ensures you didn't forget any [TODO] in the text
- `test_minimum_techniques`: Verifies (through yaml metadata) that at least 2 techniques were listed

**How to validate:**

```bash
pytest tests/test_prompts.py
```

## Required Project Structure

Fork the base repository: Click here for the template

```
desafio-prompt-engineer/
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── README.md                 # Your process documentation
│
├── prompts/
│   ├── bug_to_user_story_v1.yml       # Initial prompt (after pull)
│   └── bug_to_user_story_v2.yml       # Your optimized prompt
│
├── src/
│   ├── pull_prompts.py       # Pull from LangSmith
│   ├── push_prompts.py       # Push to LangSmith
│   ├── evaluate.py           # Automatic evaluation
│   ├── metrics.py            # 4 implemented metrics
│   ├── dataset.py            # 15 bug examples
│   └── utils.py              # Helper functions
│
├── tests/
│   └── test_prompts.py       # Validation tests
```

**What you will create:**

- `prompts/bug_to_user_story_v2.yml` - Your optimized prompt
- `tests/test_prompts.py` - Your validation tests
- `src/pull_prompt.py` - Pull script from fullcycle repository
- `src/push_prompt.py` - Push script to your repository
- `README.md` - Documentation of your optimization process

**What comes ready:**

- Dataset with 15 bugs (5 simple, 7 medium, 3 complex)
- 4 specific metrics for Bug to User Story
- Multi-provider support (OpenAI and Gemini)

## Useful Repositories

- Challenge boilerplate repository
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [VirtualEnv for Python](https://docs.python.org/3/library/venv.html)

## VirtualEnv for Python

Create and activate a virtual environment before installing dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Execution Order

### 1. Execute pull of bad prompts
```bash
python src/pull_prompts.py
```

### 2. Refactor prompts
Manually edit the file `prompts/bug_to_user_story_v2.yml` applying the techniques learned in the course.

### 3. Push optimized prompts
```bash
python src/push_prompts.py
```

### 4. Execute evaluation
```bash
python src/evaluate.py
```

## Deliverable

Public repository on GitHub (fork of the base repository) containing:
- All implemented source code
- File `prompts/bug_to_user_story_v2.yml` 100% filled and functional
- File `README.md` updated with:

### README.md must contain:

**A) Section "Applied Techniques (Phase 2)":**
- Which advanced techniques you chose to refactor the prompts
- Justification for why you chose each technique
- Practical examples of how you applied each technique

**B) Section "Final Results":**
- Public link to your LangSmith dashboard showing evaluations
- Screenshots of evaluations with minimum scores of 0.9 achieved
- Comparative table: bad prompts (v1) vs optimized prompts (v2)

**C) Section "How to Execute":**
- Clear and detailed instructions on how to execute the project
- Prerequisites and dependencies
- Commands for each project phase

### 3. Evidence in LangSmith

Public link (or screenshots) of the LangSmith dashboard. Must be visible:
- Evaluation dataset with ≥ 20 examples
- Executions of v1 prompts (bad) with low scores
- Executions of v2 prompts (optimized) with scores ≥ 0.9
- Detailed tracing of at least 3 examples

## Final Tips

- Remember the importance of specificity, context and persona when refactoring prompts
- Use Few-shot Learning with 2-3 clear examples to drastically improve performance
- Chain of Thought (CoT) is excellent for tasks requiring complex reasoning (like PR analysis)
- Use LangSmith Tracing as your main debugging tool - it shows exactly what the LLM is "thinking"
- Do not modify the evaluation datasets
- Iterate, iterate, iterate - it's normal to need 3-5 iterations to reach 0.9 on all metrics
- Document your process - the optimization journey is as important as the final result
