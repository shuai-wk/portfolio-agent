import json
import sys
from collections.abc import Iterator


def is_protected(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if "/migrations/" in normalized:
        return True
    base = normalized.rsplit("/", 1)[-1]
    return base == ".env" or base.startswith(".env.")


def find_protected_paths(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from find_protected_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_protected_paths(child)
    elif isinstance(value, str) and ("/" in value or "\\" in value):
        if is_protected(value):
            yield value


def main() -> None:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    blocked = list(find_protected_paths(tool_input))
    if blocked:
        result = {
            "continue": False,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Blocked protected path(s): " + ", ".join(blocked),
            },
        }
    else:
        result = {"continue": True}
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
