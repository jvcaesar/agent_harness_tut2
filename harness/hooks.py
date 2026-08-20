# Hooks - the extensibility seam
# pre - post - allow - deny
# fire_pre - before dispatch, short circuits on first deny
# fire_post - after dispatch, audit/log only
# hookContext - tool_name, tool_input, tool_output
from dataclasses import dataclass
from typing import Callable, Literal

HookDecision = Literal["allow", "deny"]

@dataclass
class HookContext:
    tool_name: str
    tool_input: dict
    tool_output: object | None = None

class Hooks:
    def __init__(self) -> None:
        self._pre: list[Callable[[HookContext], HookDecision]] = []
        self._post: list[Callable[[HookContext], None]] = []
        
    def add_pre(self, hook): self._pre.append(hook)
    def add_post(self, hook): self._post.append(hook)
    
    def fire_pre(self, ctx: HookContext) -> HookDecision:
        for hook in self._pre:
            if hook(ctx) == "deny":
                return "deny"
        return "allow"
    
    def fire_post(self, ctx: HookContext) -> None:
        for hook in self._post:
            hook(ctx)