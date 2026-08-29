"""Interactive command-line entry point for the agent harness."""

from __future__ import annotations

from collections.abc import Callable
import os
import re

from harness import Harness
from harness.model import OllamaModel, OpenAIModel, build_model_from_env, describe_active_model


EXIT_COMMANDS = {"exit", "bye", "quit"}


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
) -> None:
    """Run a conversation until the user requests exit or input is interrupted."""
    messages: list[dict[str, str]] = []

    while True:
        try:
            user_input = input_fn("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            output_fn("Goodbye.")
            return

        if user_input.lower() in EXIT_COMMANDS:
            output_fn("Goodbye.")
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
            output_fn(friendly_message)
            if os.getenv("HARNESS_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
                output_fn(f"Diagnostic detail: {redact_error_detail(str(exc))}")
            continue
        output_fn(f"AI> {response}")


def main() -> None:
    """Configure and start the interactive agent harness."""
    model = build_model_from_env()
    print(f"Active model: {describe_active_model()}")
    print("Type exit, bye, or quit to end the chat.")

    harness = Harness(model=model, cwd=".", max_iterations=10)
    run_interactive_chat(harness)


if __name__ == "__main__":
    main()