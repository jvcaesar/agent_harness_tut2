from collections.abc import Callable, Sequence
from typing import Any, Protocol, runtime_checkable


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
