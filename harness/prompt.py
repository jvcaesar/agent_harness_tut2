# System prommpt assembly, walks directory upwards and looks for instruction files at each level(agents.md, etc) + stitch together the system prompt
# Static scaffold first, dynamic context after
# 

from pathlib import Path


STATIC_SCAFFOLD = """You are a helpful software engineering agent.
Use the available tools carefully, respect their permission requirements, and report results clearly."""
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md", "agent.md", "claude.md")


def _walk_ancestors(path: Path):
    current = path.resolve()
    while True:
        yield current
        if current.parent == current:
            return
        current = current.parent


def assemble_system_prompt(
    cwd: str | Path,
    max_per_file: int = 4_000,
    max_total: int = 20_000,
    ) -> str:
    """
    Assemble the system prompt for the model by combining static and dynamic components.
    """
    parts: list[str] = [STATIC_SCAFFOLD]
    # Static scaffold
    total_dynamic_length = 0
    for directory in _walk_ancestors(Path(cwd)):
        for fname in INSTRUCTION_FILES:
            fpath = directory / fname
            if fpath.exists():
                remaining = max_total - total_dynamic_length
                if remaining <= 0:
                    break
                content = fpath.read_text(encoding="utf-8")[:max_per_file]
                content = content[:remaining]
                parts.append(f"\n# {fname} (from {directory})\n{content}")
                total_dynamic_length += len(content)
    return "\n".join(parts)

