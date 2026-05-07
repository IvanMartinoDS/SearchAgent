import os
import wikipedia
from ddgs import DDGS
from datetime import datetime
import textwrap
from config import OUTPUT_DIR

def _get_unique_filepath(directory: str, filename: str, extension: str) -> str:
    filepath = os.path.join(directory, f"{filename}.{extension}")
    if not os.path.exists(filepath):
        return filepath
    counter = 2
    while os.path.exists(os.path.join(directory, f"{filename}_{counter}.{extension}")):
        counter += 1
    return os.path.join(directory, f"{filename}_{counter}.{extension}")


def search_web(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No results found."
            output = ""
            for r in results:
                output += f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r['body']}\n\n"
            return output
    except Exception as e:
        return f"Web search failed: {str(e)}"


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information."""
    try:
        summary = wikipedia.summary(query, sentences=10)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=10)
            return summary
        except Exception:
            return f"Wikipedia disambiguation error: {str(e)}"
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"


def save_to_txt(content: str, filename: str) -> str:
    """Save research content to a TXT file."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = filepath = _get_unique_filepath(OUTPUT_DIR, filename, "txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        wrapped_content = "\n".join(
            textwrap.fill(line, width=100) if line.strip() else line
            for line in content.splitlines()
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Research Output - {timestamp}\n")
            f.write("=" * 100 + "\n\n")
            f.write(wrapped_content)
        return f"Content saved to {filepath}"
    except Exception as e:
        return f"Failed to save TXT: {str(e)}"


def save_to_md(content: str, filename: str) -> str:
    """Save research content to a Markdown file."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = filepath = _get_unique_filepath(OUTPUT_DIR, filename, "md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Research Output\n\n")
            f.write(f"**Date:** {timestamp}\n\n")
            f.write("---\n\n")
            f.write(content)
        return f"Content saved to {filepath}"
    except Exception as e:
        return f"Failed to save MD: {str(e)}"