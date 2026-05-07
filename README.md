# SearchAgent

This is a quick - 30 minutes - code for a Search Agent.

This is a research assistant powered by Google Gemini and Anthropic Claude that uses web and Wikipedia search tools to gather and summarize information.

---

## Setup

### 1. Configure API Keys

Create a `.env` file in the root of the project and add your API keys:

```env
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

> Get your keys here: [Google AI Studio](https://aistudio.google.com/app/apikey) | [Anthropic Console](https://console.anthropic.com/)

---

### 2. Configure [`config.py`](./config.py)

**Output folder** — set the folder where search results will be saved:

```python
OUTPUT_DIR = "search_output"
```

Then add the same folder name to your [`.gitignore`](./.gitignore) to avoid committing generated files:

```gitignore
# Output directory for research results
search_output/
```

**Models** — select the models you want to use:

```python
GEMINI_MODEL = "gemini-2.0-flash-lite"
ANTHROPIC_MODEL = "claude-opus-4-5"
```

> Available models: [Gemini models](https://ai.google.dev/gemini-api/docs/models/gemini) | [Anthropic models](https://docs.anthropic.com/en/docs/about-claude/models/all-models)

---

### 3. Create the Environment

> ⚠️ Python **3.10** is required due to compatibility requirements of the LLMs used (`google-genai`, `anthropic`).

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 4. Run
Finally, you can run your solution by typing in the terminal
```bash
python main.py
```