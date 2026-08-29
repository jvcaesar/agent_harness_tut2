# Notes

Notes and observations collected while running and testing the agent.

## Feature requests

| Status | Request |
| --- | --- |
| ❌ Not started | An agent explainer to know what it's doing behind the scene. Like its reasoning, actions, etc. |
| 🟡 Partial | A context cleaner, so the whole history and interactions is not being sent to the model for every user query. Send the history if it's relevant to the user query, or parts of it, or none of it. `ContextManager.compact_if_needed` (`harness/context.py`) trims by a fixed threshold, not by relevance to the query. |
| ✅ Done (2026-08-29) | If I tell the agent my name and give it a name as well, then it could use that info in the query/response instead of using "you" and "AI" for the input and response. See `FEATURES.md`. |
| ❌ Not started | There is no verifier or reviewer of the model's answer. The model goes through max 10 iterations and stops abruptly when the limit is hit. It could have a more relevant and user friendly answer based on what it has done until that point, and also make suggestions on how to proceed to solve the user query if it's incomplete or not answered. |
| ✅ Done | Can the output to terminal have user friendly colors or other formatting possibilities to make it visually appealing. `TerminalFormatter` (`agent.py`) already applies ANSI colors when the terminal supports them. |
| ❌ Not started | (This may need a good model, or I have to be very specific in the ask and verify it.) Can I make the agent do changes to its own code? |
| ❌ Not started | Kill itself and restart with the same session history? |

Legend: ✅ Done · 🟡 Partial · ❌ Not started. Update the status and add a date when a request
is implemented or picked up; see `FEATURES.md` for implementation details of completed items.
