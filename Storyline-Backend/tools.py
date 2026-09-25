import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

SANDBOX_DIR = Path(__file__).parent / "sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)

search_tool = TavilySearch(max_results=5)


@tool
def save_markdown_file(filename: str, content: str) -> str:
    """Save the given content as a markdown (.md) file inside the sandbox folder."""
    if not filename.endswith(".md"):
        filename += ".md"
    file_path = SANDBOX_DIR / filename
    file_path.write_text(content, encoding="utf-8")
    return f"Saved file: {filename}"


@tool
def read_markdown_file(filename: str) -> str:
    """Read and return the content of a markdown (.md) file from the sandbox folder."""
    if not filename.endswith(".md"):
        filename += ".md"
    file_path = SANDBOX_DIR / filename
    if not file_path.exists():
        return f"File not found: {filename}"
    return file_path.read_text(encoding="utf-8")


tools = [search_tool, save_markdown_file, read_markdown_file]