"""Interactive command-line entry point for the agent harness."""

from __future__ import annotations

from collections.abc import Callable
import os
import re
import sys

from harness import Harness
from harness.model import OllamaModel, OpenAIModel, build_model_from_env, describe_active_model


EXIT_COMMANDS = {"exit", "bye", "quit"}
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"


class TerminalFormatter:
    """Format interactive chat output when the active terminal supports color."""

    def __init__(self, color: bool | None = None, user_name: str = "You", agent_name: str = "AI") -> None:
        self.color = color if color is not None else sys.stdout.isatty() and not os.getenv("NO_COLOR")
        self.user_name = user_name
        self.agent_name = agent_name

    def text(self, label: str, message: str, color_code: str = "") -> str:
        if not self.color:
            return f"{label}{message}"
        return f"{BOLD}{color_code}{label}{RESET}{message}"

    def prompt(self) -> str:
        return self.text(f"{self.user_name}> ", "", CYAN)

    def response(self, message: str) -> str:
        return self.text(f"{self.agent_name}> ", message, GREEN)

    def error(self, message: str) -> str:
        return self.text(f"{self.agent_name} error: ", message, RED)

    def info(self, message: str) -> str:
        return self.text("", message, YELLOW)


def format_model_error(error: Exception, model: object) -> str:
    """Convert provider failures into concise, actionable chat messages."""
    detail = str(error)
    detail_lower = detail.lower()

    if isinstance(model, OllamaModel):
        provider = "Ollama"
        endpoint = model.base_url
        if "timeout" in detail_lower:
            return f"AI is unavailable: {provider} timed out after {model.timeout:g} seconds. Try again or increase OLLAMA_TIMEOUT."
        if any(term in detail_lower for term in ("connection", "connect", "refused")):
            return f"AI is unavailable: {provider} could not be reached at {endpoint}. Start Ollama with `ollama serve`, then try again."
        if "not found" in detail_lower or "404" in detail_lower:
            return f"AI is unavailable: the Ollama model '{model.model}' was not found. Run `ollama pull {model.model}`, then try again."

    if isinstance(model, OpenAIModel):
        provider = "OpenAI"
        if any(term in detail_lower for term in ("authentication", "unauthorized", "401", "api key")):
            return "AI is unavailable: OpenAI authentication failed. Check OPENAI_API_KEY in .env, then restart the agent."
        if any(term in detail_lower for term in ("rate limit", "429")):
            return "AI is unavailable: OpenAI rate limit reached. Wait a moment, then try again."
        if "timeout" in detail_lower:
            return f"AI response failed: the request timed out after {model.timeout:g} seconds. Try again or increase OPENAI_TIMEOUT."
        if any(term in detail_lower for term in ("connection", "connect")):
            return "AI is unavailable: OpenAI could not be reached. Check your network connection, then try again."

    if "json" in detail_lower or "response" in detail_lower:
        return "AI response failed: the provider returned an unexpected response. Try again later."
    return "AI response failed unexpectedly. Try again, or set HARNESS_DEBUG=true to see diagnostic details."


def redact_error_detail(detail: str) -> str:
    """Remove common secret formats before persisting diagnostic details."""
    detail = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", detail)
    return re.sub(r"(?i)(api[_ -]?key|authorization)\s*[=:]\s*\S+", r"\1=[REDACTED]", detail)


def run_interactive_chat(
    harness: Harness,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    formatter: TerminalFormatter | None = None,
) -> None:
    """Run a conversation until the user requests exit or input is interrupted."""
    messages: list[dict[str, str]] = []
    formatter = formatter or TerminalFormatter(color=False)

    while True:
        try:
            user_input = input_fn(formatter.prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            output_fn(formatter.info("Goodbye."))
            return

        if user_input.lower() in EXIT_COMMANDS:
            output_fn(formatter.info("Goodbye."))
            return
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            response = harness.run_turn(messages)
        except Exception as exc:
            friendly_message = format_model_error(exc, harness.model)
            harness.persistence.append_event({
                "event": "model_error",
                "model": harness.model.__class__.__name__,
                "message": friendly_message,
                "detail": redact_error_detail(str(exc)),
            })
            output_fn(formatter.error(friendly_message))
            if os.getenv("HARNESS_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
                output_fn(formatter.error(f"Diagnostic detail: {redact_error_detail(str(exc))}"))
            continue
        output_fn(formatter.response(response))


def main() -> None:
    """Configure and start the interactive agent harness."""
    plain_formatter = TerminalFormatter()
    print(plain_formatter.info("Agent Harness"))
    user_name = input(plain_formatter.text("Your name (optional): ", "", CYAN)).strip() or "You"
    agent_name = input(plain_formatter.text("Name this agent (optional): ", "", CYAN)).strip() or "AI"

    formatter = TerminalFormatter(user_name=user_name, agent_name=agent_name)
    model = build_model_from_env()
    print(formatter.text("Active model: ", describe_active_model(), CYAN))
    print(formatter.info("Type exit, bye, or quit to end the chat."))

    harness = Harness(model=model, cwd=".", max_iterations=10, user_name=user_name, agent_name=agent_name)
    run_interactive_chat(harness, formatter=formatter)


if __name__ == "__main__":
    main()