from __future__ import annotations

from pathlib import Path

from harness import Harness
from harness.model import DummyModel, end_turn, tool_call


def _scripted_policy(system_prompt: str, messages: list[dict], tool_descriptors: list[dict]) -> dict:
    target = Path(__file__).resolve().parent / "main.py"
    last = messages[-1].get("content", "") if messages else ""

    if "tool_result" not in last:
        return tool_call(
            "read_file",
            {"path": str(target)},
        )

    if "return a - b" in target.read_text(encoding="utf-8"):
        return tool_call(
            "edit_file",
            {
                "path": str(target),
                "find": "return a - b",
                "replace": "return a + b",
            },
        )

    return end_turn("Demo completed successfully. Testing passed.")


def run_demo(project_dir: str | Path | None = None) -> str:
    project_root = Path(project_dir) if project_dir is not None else Path(__file__).resolve().parent
    main_path = project_root / "main.py"

    if not main_path.exists():
        main_path.write_text("def add(a, b):\n    \"\"\"Return the sum of two numbers.\"\"\"\n    return a - b\n", encoding="utf-8")

    model = DummyModel(policy=_scripted_policy)
    harness = Harness(model=model, cwd=project_root, max_iterations=5)
    result = harness.run("Fix the bug in demo/main.py so the tests pass.")

    import subprocess
    completed = subprocess.run(
        ["python", "-m", "unittest", "-q", str(project_root / "test_main.py")],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode == 0:
        return f"Demo passed: {result} | {completed.stdout.strip()}"
    return f"Demo failed: {result} | {completed.stderr.strip()}"


if __name__ == "__main__":
    print(run_demo())
