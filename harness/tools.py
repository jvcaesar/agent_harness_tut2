# tool registry - the dispatch table
# name -> permission -> handler
# Skills are registred in the same way as tools, but they are not called directly by the model. Instead, they are called by the handlers that read the markdown files at invocation time.
# Skills are a way to compose tools into higher-level operations.
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from harness.permissions import Permission


@dataclass
class Tool:
    """
    A class to represent a tool with its name, permission, and handler.
    """
    name: str  # The name of the tool
    permission: str  # The permission required to use the tool
    handler: Callable  # The function that handles the tool's operation
    description: str = ""  # A brief description of the tool
    input_schema: dict | None = None


@dataclass
class Skill(Tool):
    """A markdown-backed skill that resolves its body at invocation time."""
    source: str = ""

    def invoke(self, args: dict) -> str:
        if not self.source:
            return ""
        path = Path(self.source)
        if not path.exists():
            return f"Skill source not found: {self.source}"
        text = path.read_text(encoding="utf-8")
        return text.strip() or ""


class ToolRegistry:
    """
    A class to manage the registry of tools, allowing for registration and retrieval of tools.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register_tool(
        self,
        name: str,
        permission: str,
        handler: Callable,
        description: str = "",
        input_schema: dict | None = None,
    ) -> None:
        """
        Register a new tool in the registry.

        Args:
            name (str): The name of the tool.
            permission (str): The permission required to use the tool.
            handler (callable): The function that handles the tool's operation.
            description (str, optional): A brief description of the tool. Defaults to "".
        """
        self._tools[name] = Tool(name, permission, handler, description, input_schema)

    def register_skill(self, name: str, permission: str, source: str, description: str = "") -> None:
        self._tools[name] = Skill(name=name, permission=permission, handler=lambda args: self._tools[name].invoke(args), description=description, source=source)

    def get_tool(self, name: str) -> Tool | None:
        """
        Retrieve a tool by its name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            Tool: The requested tool.
        """
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def descriptors(self) -> list[dict]:
        """
        Get a list of descriptors for all registered tools.

        Returns:
            list: A list of dictionaries containing tool names and descriptions.
        """
        return [
            {
                "name": tool.name,
                "permission": tool.permission,
                "description": tool.description,
                "input_schema": tool.input_schema or {"type": "object", "properties": {}},
            }
            for tool in self._tools.values()
        ]


def register_core_tools(registry: ToolRegistry | None = None) -> ToolRegistry:
    from harness.builtins import bash, edit_file, grep, list_dir, read_file, write_file

    registry = registry or ToolRegistry()
    registry.register_tool(
        "list_tools",
        Permission.READ_ONLY,
        lambda args: "\n".join(
            f"{tool['name']}: {tool['description']} (permission: {tool['permission']})"
            for tool in registry.descriptors()
        ),
        "List the tools available to the agent.",
    )
    registry.register_tool(
        "read_file",
        Permission.READ_ONLY,
        lambda args: read_file(args["path"]),
        "Read a file from disk.",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    )
    registry.register_tool(
        "grep",
        Permission.READ_ONLY,
        lambda args: grep(args["pattern"], args["path"]),
        "Search for a pattern in a file.",
        {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]},
    )
    registry.register_tool(
        "list_dir",
        Permission.READ_ONLY,
        lambda args: list_dir(args.get("path", ".")),
        "List the files and subdirectories in a directory.",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
    )
    registry.register_tool(
        "write_file",
        Permission.WORKSPACE,
        lambda args: write_file(args["path"], args["content"]),
        "Write text to a file.",
        {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    )
    registry.register_tool(
        "edit_file",
        Permission.WORKSPACE,
        lambda args: edit_file(args["path"], args["find"], args["replace"]),
        "Replace text in a file.",
        {"type": "object", "properties": {"path": {"type": "string"}, "find": {"type": "string"}, "replace": {"type": "string"}}, "required": ["path", "find", "replace"]},
    )
    registry.register_tool(
        "bash",
        Permission.FULL,
        lambda args: bash(args["command"], int(args.get("timeout", 10)), args.get("cwd")),
        "Run a shell command with full permission.",
        {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["command"]},
    )
    return registry