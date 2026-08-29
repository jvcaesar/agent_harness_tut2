# A component of the harness that runs a loop until a goal is achieved.
# decide, dispatch, feedback, terminate
# the only file that calls the model
# this is the entire engine of the harness, it is responsible for running the loop until the goal is achieved.

from pathlib import Path

from harness.context import ContextManager
from harness.hooks import HookContext, Hooks
from harness.permissions import Permission, bash_denial_reason, can_dispatch
from harness.persistence import SessionPersistence
from harness.prompt import assemble_system_prompt
from harness.tools import ToolRegistry, register_core_tools


class Harness:
    def __init__(
        self,
        model,
        cwd: str | Path | None = None,
        max_iterations: int = 10,
        context: ContextManager | None = None,
        tools: ToolRegistry | None = None,
        hooks: Hooks | None = None,
        persistence: SessionPersistence | None = None,
        permission: str = Permission.WORKSPACE,
        user_name: str | None = None,
        agent_name: str | None = None,
    ) -> None:
        self.model = model
        self.cwd = Path(cwd or ".").resolve()
        self.max_iterations = max_iterations
        self.context = context or ContextManager()
        self.tools = tools or register_core_tools(ToolRegistry())
        self.hooks = hooks or Hooks()
        self.persistence = persistence or SessionPersistence(self.cwd / ".harness" / "session.jsonl")
        self.permission = permission
        self.user_name = user_name
        self.agent_name = agent_name

    def run(self, goal: str) -> str:
        """
        Run the loop until the goal is achieved.

        Args:
            goal (str): The goal to achieve.

        Returns:
            str: The result of the loop.
        """
        system_prompt = assemble_system_prompt(self.cwd, user_name=self.user_name, agent_name=self.agent_name)
        messages = [{"role": "user", "content": goal}]
        return self.run_turn(messages, system_prompt=system_prompt)

    def run_turn(self, messages: list[dict], system_prompt: str | None = None) -> str:
        """Process one model turn using the supplied conversation history."""
        system_prompt = system_prompt or assemble_system_prompt(self.cwd, user_name=self.user_name, agent_name=self.agent_name)
        result = ""

        for _ in range(1, self.max_iterations + 1):
            messages = self.context.compact_if_needed(messages)
            response = self.model(system_prompt, messages, self.tools.descriptors())

            if response.get("stop_reason") == "end_turn":
                text = response.get("text", "")
                messages.append({"role": "assistant", "content": text})
                return text

            tool_call = response.get("tool_call") or {}
            result = self._dispatch_tool(tool_call)
            messages.append({"role": "user", "content": f"tool_result: {result}"})

        return f"(Stopped after {self.max_iterations} iterations) {result}"

    def _dispatch_tool(self, tool_call: dict) -> str:
        if not isinstance(tool_call, dict):
            return "Malformed tool call"

        name = str(tool_call.get("name", ""))
        arguments = tool_call.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        path_denial = self._validate_workspace_paths(name, arguments)
        if path_denial:
            return f"Tool denied: {path_denial}"

        if name == "bash":
            command = str(arguments.get("command", ""))
            denial_reason = bash_denial_reason(command)
            if denial_reason:
                return f"Tool denied: bash command blocked because {denial_reason}."
            arguments["cwd"] = str(self.cwd)

        tool = self.tools.get_tool(name)
        if tool is None:
            return f"Unknown tool: {name}"

        if not can_dispatch(tool.permission, self.permission):
            return f"Permission denied: {name} requires {tool.permission} permission, but the harness is configured for {self.permission}."

        hook_context = HookContext(tool_name=name, tool_input=arguments)
        if self.hooks.fire_pre(hook_context) == "deny":
            return f"Tool denied: {name} was blocked by a pre-dispatch safety hook."

        try:
            output = tool.handler(arguments)
        except Exception as exc:  # pragma: no cover - defensive path
            output = f"Tool execution failed: {exc}"

        hook_context.tool_output = output
        self.hooks.fire_post(hook_context)
        self.persistence.append_event({
            "event": "tool_call",
            "tool": name,
            "arguments": arguments,
            "result": str(output),
        })
        return str(output)

    def _validate_workspace_paths(self, name: str, arguments: dict) -> str | None:
        path_argument_names = {
            "read_file": ("path",),
            "write_file": ("path",),
            "edit_file": ("path",),
            "grep": ("path",),
        }
        for argument_name in path_argument_names.get(name, ()):
            value = arguments.get(argument_name)
            if not isinstance(value, str) or not value:
                continue
            path = Path(value)
            resolved_path = (self.cwd / path).resolve() if not path.is_absolute() else path.resolve()
            try:
                resolved_path.relative_to(self.cwd)
            except ValueError:
                return f"{name} cannot access '{value}' because it is outside the workspace '{self.cwd}'."
            arguments[argument_name] = str(resolved_path)
        return None
