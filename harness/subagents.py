# Sub-agent archetypes for the harness. 3 presets -> explore, general and verify
# no infinite spawning of sub-agents, they are spawned by the main agent and terminated when the goal is achieved or the loop ends.

class SubAgentRegistry:
    """
    A registry for managing sub-agent archetypes in the harness.
    """
    PRESETS = {
        "explore": SubAgentSpec(
            name="explore",
            permission=Permission.READONLY,
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
            tools=("read_file", "bash","grep"),
            system_prompt="You are a verification agent. Your goal is to verify information and ensure accuracy. Confirm a change with tests.",
        )
    }