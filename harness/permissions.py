# Permissions - 3 tier, dynamic for bash
# On top of static rules, the agent asks before dangerous calls

import shlex
import re


class Permission:
    READ_ONLY = "read"
    WORKSPACE = "workspace"
    FULL = "full"


RANK = {Permission.READ_ONLY: 1, Permission.WORKSPACE: 2, Permission.FULL: 3}

_READ_CMDS = {"ls", "cat", "head", "grep", "find", "wc", "echo", "pwd", "whoami"}
_DANGER_CMDS = {"rm", "sudo", "mv", "kill", "shutdown", "dd", "chmod", "chown"}
_DENIED_BASH_PATTERNS = {
    r"\brm\s+.*(?:-r|-R|--recursive)": "recursive deletion is not allowed",
    r"\b(?:del|erase|rd|rmdir)\b.*(?:/s|/S)": "recursive deletion is not allowed",
    r"\bremove-item\b.*(?:-recurse|-r)": "recursive deletion is not allowed",
    r"\b(?:format|diskpart|clear-disk)\b": "disk formatting is not allowed",
    r"\b(?:shutdown|restart-computer|stop-computer)\b": "system shutdown or restart is not allowed",
    r"\b(?:invoke-webrequest|curl|wget)\b.*(?:\||;).*\b(?:iex|bash|sh|powershell)\b": "download-and-execute commands are not allowed",
}


def classify_bash(cmd: str) -> str:
    parts = shlex.split(cmd) if cmd else []
    if not parts:
        return Permission.READ_ONLY
    if parts[0] in _READ_CMDS:
        return Permission.READ_ONLY
    if parts[0] in _DANGER_CMDS:
        return Permission.FULL
    return Permission.WORKSPACE


def bash_denial_reason(command: str) -> str | None:
    """Return a safety explanation when a shell command is always denied."""
    for pattern, reason in _DENIED_BASH_PATTERNS.items():
        if re.search(pattern, command, flags=re.IGNORECASE):
            return reason
    return None


def can_dispatch(required: str, current: str) -> bool:
    return RANK.get(current, 0) >= RANK.get(required, 0)
