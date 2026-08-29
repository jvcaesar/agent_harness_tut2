import json
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from dotenv import load_dotenv


@runtime_checkable
class Model(Protocol):
    def __call__(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tool_descriptors: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        ...


def end_turn(text: str = "") -> dict[str, Any]:
    return {"stop_reason": "end_turn", "text": text}


def tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "stop_reason": "tool_call",
        "text": "",
        "tool_call": {"name": name, "arguments": arguments},
    }


class DummyModel:
    """
    Deterministic offline model for tests and local harness development.

    By default it ends the turn immediately. For scripted behavior, pass a
    policy callable or a finite list of response dictionaries.
    """

    def __init__(
        self,
        policy: Callable[[str, list[dict[str, Any]], Sequence[dict[str, Any]]], dict[str, Any]] | None = None,
        scripted_responses: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        self._policy = policy
        self._scripted_responses = list(scripted_responses or [])
        self.calls = 0

    def __call__(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tool_descriptors: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        self.calls += 1

        if self._policy is not None:
            response = self._policy(system_prompt, messages, tool_descriptors)
            return self._normalize(response)

        if self._scripted_responses:
            response = self._scripted_responses.pop(0)
            return self._normalize(response)

        return end_turn("DummyModel default response")

    def _normalize(self, response: dict[str, Any]) -> dict[str, Any]:
        stop_reason = response.get("stop_reason")
        if stop_reason == "tool_call":
            call = response.get("tool_call") or {}
            name = str(call.get("name", ""))
            arguments = call.get("arguments")
            if not isinstance(arguments, dict):
                arguments = {}
            return tool_call(name, arguments)

        return end_turn(str(response.get("text", "")))


class OllamaModel:
    """Thin local-model adapter for Ollama-compatible endpoints."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __call__(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tool_descriptors: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            import requests
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError("requests is required for OllamaModel") from exc

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + [
                {"role": msg.get("role", "user"), "content": str(msg.get("content", ""))}
                for msg in messages
            ],
            "stream": False,
            "tools": [
                {"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]}}
                for tool in tool_descriptors
            ],
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        text = ""
        if isinstance(result, dict):
            message = result.get("message") or {}
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                call = tool_calls[0].get("function", {})
                arguments = call.get("arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                return tool_call(str(call.get("name", "")), arguments if isinstance(arguments, dict) else {})
            text = str(message.get("content", ""))
        return end_turn(text)


class OpenAIModel:
    """Thin OpenAI-compatible model adapter for hosted LLM usage."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.timeout = timeout

    def __call__(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tool_descriptors: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("openai package is required for OpenAIModel") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(
            {"role": msg.get("role", "user"), "content": str(msg.get("content", ""))}
            for msg in messages
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=payload_messages,
            tools=[
                {"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]}}
                for tool in tool_descriptors
            ],
        )
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0].function
            try:
                arguments = json.loads(call.arguments)
            except json.JSONDecodeError:
                arguments = {}
            return tool_call(call.name, arguments if isinstance(arguments, dict) else {})
        content = message.content or ""
        return end_turn(content)


def build_model_from_env() -> Model:
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    ollama_enabled = os.getenv("OLLAMA_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    if ollama_enabled:
        model = OllamaModel(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=float(os.getenv("OLLAMA_TIMEOUT", "60")),
        )
        return model

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        model = OpenAIModel(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL"),
            timeout=float(os.getenv("OPENAI_TIMEOUT", "60")),
        )
        return model

    return DummyModel()


def describe_active_model() -> str:
    model = build_model_from_env()
    name = model.__class__.__name__

    if isinstance(model, OllamaModel):
        return f"{name} ({model.model})"
    if isinstance(model, OpenAIModel):
        return f"{name} ({model.model})"
    return f"{name}"
