# JSONL session persistence, append only, no overwriting, no reading, no deleting
# every event, one line, flushed on every write, no buffering, no caching, no reading, no deleting
# Can also use markdowns

from pathlib import Path

from streamlit import json


class SessionPersistence:
    """
    A class for persisting session events in JSONL format.

    This class provides methods to append events to a JSONL file, ensuring that each event is written on a new line.
    It does not support reading, deleting, or overwriting existing events.

    Attributes:
        file_path (str): The path to the JSONL file where events will be persisted.
    """

    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize the SessionPersistence instance.

        Args:
            file_path (str | Path): The path to the JSONL file where events will be persisted.
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

    def append_event(self, event: dict) -> None:
        """
        Append an event to the JSONL file.

        Args:
            event (dict): The event data to be persisted. It should be serializable to JSON.
        """
        line = json.dumps(event, ensure_ascii=False, default=str) + '\n'
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(line)
            f.flush()  # Ensure the data is written to disk immediately
            
    def replay(self) -> list[dict]:
        """
        Replay the events from the JSONL file.

        Returns:
            list[dict]: A list of events read from the JSONL file.
        """
        if not self.file_path.exists():
            return []
        
        events = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    continue  # Skip lines that are not valid JSON
        return events