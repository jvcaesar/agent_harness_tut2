# Permissions - 3 tier, dynamic for bash
# On top of static rules, the agent asks before dangerous calls

import shlex


class Permission:
    READ_ONLY = "read"
    WORKSPACE = "workspace"
    FULL = "full"
        
RANK = {Permission.READ_ONLY: 1, Permission.WORKSPACE: 2, Permission.FULL: 3}

_READ_CMDS = {"ls", "cat", "head", "grep", "find", "wc", "echo", ...}
_DANGER_CMDS = {"rm", "sudo", "mv", "kill", "shutdown", "dd", ...}

def classify_bash(cmd:str) -> str:
    parts = shlex.split(cmd) if cmd else []
    if not parts: return Permission.READ_ONLY
    if parts[0] in _READ_CMDS: return Permission.READ_ONLY
    if parts[0] in _DANGER_CMDS: return Permission.FULL
    return Permission.WORKSPACE

def can_dispatch(required: str, current: str) -> bool:
    return RANK[current] > RANK[required]
