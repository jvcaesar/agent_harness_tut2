# context management for the harness, including compacting messages and managing the conversation history.
# triggered when the trajectory grows past the threshold
# in Production, swap the heuristic for a model-based summarization of the conversation history, to keep the context relevant and concise.

from dataclasses import dataclass


@dataclass
class ContextManager:
    """
    A class to manage the context of the conversation, including compacting messages and managing the conversation history.
    """
    compact_threshold: int = 18  # Maximum number of messages to keep in context
    keep_recent: int = 5  # Number of recent messages to keep when compacting

    def _summarize(self, messages: list[dict]) -> dict:
        text = " ".join(str(msg.get("content", "")) for msg in messages)
        return {"role": "system", "content": f"Summary of earlier context: {text[:500]}"}

    def compact_if_needed(self, messages: list[dict]) -> list[dict]:
        """
        Compact the messages if they exceed the maximum allowed.

        Args:
            messages (list): The current list of messages.

        Returns:
            list: The compacted list of messages.
        """
        if len(messages) < self.compact_threshold:
            return messages

        older = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]
        summary = self._summarize(older)
        return [summary] + recent
