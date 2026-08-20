# tool registry - the dispatch table
# name -> permission -> handler
# Skills are registred in the same way as tools, but they are not called directly by the model. Instead, they are called by the handlers that read the markdown files at invocation time. 
# Skills are a way to compose tools into higher-level operations.
from attr import dataclass

@dataclass
class Tool:
    """
    A class to represent a tool with its name, permission, and handler.
    """
    name: str  # The name of the tool
    permission: str  # The permission required to use the tool
    handler: callable  # The function that handles the tool's operation
    description: str = ""  # A brief description of the tool
    
class ToolRegistry:
    """
    A class to manage the registry of tools, allowing for registration and retrieval of tools.
    """
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register_tool(self, name: str, permission: str, handler: callable, description: str = "") -> None:
        """
        Register a new tool in the registry.

        Args:
            name (str): The name of the tool.
            permission (str): The permission required to use the tool.
            handler (callable): The function that handles the tool's operation.
            description (str, optional): A brief description of the tool. Defaults to "".
        """
        self._tools[name] = Tool(name, permission, handler, description)

    def get_tool(self, name: str) -> Tool:
        """
        Retrieve a tool by its name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            Tool: The requested tool.
        """
        return self._tools.get(name)

    def descriptors(self) -> list[dict]:
        """
        Get a list of descriptors for all registered tools.

        Returns:
            list: A list of dictionaries containing tool names and descriptions.
        """
        return [{"name": tool.name, "permission": tool.permission, "description": tool.description} for tool in self._tools.values()]