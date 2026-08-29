# Sub-agent archetypes for the harness. 3 presets -> explore, general and verify
# no infinite spawning of sub-agents, they are spawned by the main agent and terminated when the goal is achieved or the loop ends.

from dataclasses import dataclass, field

from harness.permissions import Permission


@dataclass(frozen=True)
class SubAgentSpec:
    name: str
    permission: str
    tools: tuple[str, ...]
    system_prompt: str


class SubAgentRegistry:
    """
    A registry for managing sub-agent archetypes in the harness.
    """

    PRESETS = {
        "explore": SubAgentSpec(
            name="explore",
            permission=Permission.READ_ONLY,
            tools=("read_file", "grep"),
            system_prompt="You are an explorer agent. Your goal is to explore the environment and gather information. You can only read.",
        ),
        "general": SubAgentSpec(
            name="general",
            permission=Permission.WORKSPACE,
            tools=("read_file", "grep", "write_file", "edit_file", "bash"),
            system_prompt="You are a general agent. Your goal is to assist with various tasks and operations.",
        ),
        "verify": SubAgentSpec(
            name="verify",
            permission=Permission.WORKSPACE,
            tools=("read_file", "bash", "grep"),
            system_prompt="You are a verification agent. Your goal is to verify information and ensure accuracy. Confirm a change with tests.",
        ),
    }

    def __init__(self) -> None:
        self._agents = dict(self.PRESETS)

    def register(self, name: str, spec: SubAgentSpec) -> None:
        self._agents[name] = spec

    def get(self, name: str) -> SubAgentSpec | None:
        return self._agents.get(name)

    @property
    def presets(self) -> dict[str, SubAgentSpec]:
        return dict(self._agents)

    def __iter__(self):
        return iter(self._agents.items())