# Primitives for the harness. The non-negotiable five
# read, write, edit, bash, grep

from pathlib import Path


def read_file(path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path (str): The path to the file.

    Returns:
        str: The contents of the file.
    """
    return Path(path).read_text(encoding="utf-8")

def edit_file(path: str, find: str, replace: str) -> str:
    """
    Edit a file by replacing occurrences of a string with another string.

    Args:
        path (str): The path to the file.
        find (str): The string to find in the file.
        replace (str): The string to replace the found string with.

    Returns:
        str: A message indicating the result of the edit operation.
    """
    content = Path(path).read_text(encoding="utf-8")
    if find not in content:
        raise ValueError(f"'{find}' not found in {path}")
    new_content = content.replace(find, replace)
    Path(path).write_text(new_content, encoding="utf-8")
    return f"Edited {path}: replaced '{find}' with '{replace}'"

def write_file(path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        path (str): The path to the file.
        content (str): The content to write to the file.

    Returns:
        str: A message indicating the result of the write operation.
    """
    Path(path).write_text(content, encoding="utf-8")
    return f"Wrote to {path}"

def list_dir(path: str = ".") -> str:
    """
    List the entries of a directory.

    Args:
        path (str): The directory to list. Defaults to the current directory.

    Returns:
        str: One entry per line, directories suffixed with '/', or a message if empty/not a directory.
    """
    directory = Path(path)
    if not directory.is_dir():
        return f"Not a directory: {path}"
    entries = sorted(directory.iterdir(), key=lambda entry: entry.name)
    if not entries:
        return f"{path} is empty"
    return "\n".join(entry.name + "/" if entry.is_dir() else entry.name for entry in entries)

def grep(pattern: str, path: str) -> str:
    """
    Search for a pattern in a file.

    Args:
        pattern (str): The pattern to search for.
        path (str): The path to the file.

    Returns:
        str: The lines containing the pattern, or a message if no matches are found.
    """
    content = Path(path).read_text(encoding="utf-8")
    matches = [line for line in content.splitlines() if pattern in line]
    return "\n".join(matches) if matches else f"No matches for '{pattern}' in {path}"

def bash(command: str, timeout: int = 10, cwd: str | Path | None = None) -> str:
    """
    Execute a bash command.

    Args:
        command (str): The bash command to execute.
        timeout (int, optional): The maximum time to wait for the command to complete. Defaults to 10 seconds.

    Returns:
        str: The output of the bash command.
    """
    import subprocess
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e.stderr.decode('utf-8')}"
    except subprocess.TimeoutExpired:
        return "Command timed out"