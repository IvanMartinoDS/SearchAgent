import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

GEMINI_MODEL = "gemini-2.0-flash-lite"
ANTHROPIC_MODEL = "claude-opus-4-5"

OUTPUT_DIR = "search_output"