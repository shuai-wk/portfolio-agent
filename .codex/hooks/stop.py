import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    backend = Path(__file__).resolve().parents[2] / "backend"
    venv = backend / ".venv"
    ruff = venv / "Scripts" / "ruff.exe"
    pytest = venv / "Scripts" / "pytest.exe"
    ruff_cmd = str(ruff) if ruff.exists() else (shutil.which("ruff") or "ruff")
    pytest_cmd = str(pytest) if pytest.exists() else (shutil.which("pytest") or "pytest")

    checks = [
        ("ruff", [ruff_cmd, "check", "."]),
        ("pytest", [pytest_cmd, "-q"]),
    ]
    for name, cmd in checks:
        proc = subprocess.run(cmd, cwd=backend, capture_output=True, text=True)
        output = (proc.stdout + proc.stderr).strip()
        print(f"[stop-hook] {'PASS' if proc.returncode == 0 else 'FAIL'} {name}", file=sys.stderr)
        if output:
            print(output, file=sys.stderr)

    sys.stdout.write(json.dumps({"continue": False}))


if __name__ == "__main__":
    main()
