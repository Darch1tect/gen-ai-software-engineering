from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Lorem Ipsum Server")

LOREM_FILE = Path(__file__).parent / "lorem-ipsum.md"
DEFAULT_WORD_COUNT = 30


def _load_words() -> list[str]:
    text = LOREM_FILE.read_text(encoding="utf-8")
    body_lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    return " ".join(body_lines).split()


def _first_words(word_count: int = DEFAULT_WORD_COUNT) -> str:
    if word_count < 1:
        raise ValueError("word_count must be at least 1")
    words = _load_words()
    return " ".join(words[:word_count])


@mcp.resource("lorem://ipsum")
def lorem_ipsum_default() -> str:
    """Default lorem-ipsum.md excerpt: first 30 words."""
    return _first_words(DEFAULT_WORD_COUNT)


@mcp.resource("lorem://ipsum/{word_count}")
def lorem_ipsum_with_count(word_count: int) -> str:
    """lorem-ipsum.md excerpt limited to `word_count` words."""
    return _first_words(word_count)


@mcp.tool()
def read(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Read the lorem-ipsum.md resource and return its first `word_count` words (default 30)."""
    return _first_words(word_count)


if __name__ == "__main__":
    mcp.run()
