# A component of the harness that runs a loop until a goal is achieved.
# decide, dispatch, feedback, terminate
# the only file that calls the model
# this is the entire engine of the harness, it is responsible for running the loop until the goal is achieved.

def run(self, goal:str) -> str:
    """
    Run the loop until the goal is achieved.

    Args:
        goal (str): The goal to achieve.

    Returns:
        str: The result of the loop.
    """
    system_prompt = assemble_system_prompt(self.cwd)
    messages = [
        {"role": "user", "content": goal}
    ]
    
    for step in range(1, self.max_iterations + 1):
        messages = self.context.compact_if_needed(messages)
        # self.model decides what to do next, either call a tool or end the loop
        response = self.model(system_prompt, messages, self.tools.descriptors())
        
        if response.get("stop_reason") == "end_turn":
            return response.get("text", "")
        
        #dispatch_tool calls the tool and returns the result
        result = self._dispatch_tool(response["tool_call"])
        messages.append({"role": "user", "content": f"tool_result: {result}"})
        
    return f"(Stopped after {self.max_iterations} iterations) {result}"
