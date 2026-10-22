"""Validate the repository-pinned Emscripten toolchain."""
from pathlib import Path
import re
import subprocess


def pinned_version():
    return (Path(__file__).resolve().parent.parent / ".emscripten-version").read_text().strip()


def validate_emscripten():
    expected = pinned_version()
    for compiler in ("emcc", "em++"):
        try:
            output = subprocess.check_output([compiler, "--version"], text=True)
        except (OSError, subprocess.CalledProcessError) as error:
            raise RuntimeError(f"Cannot run {compiler}. Activate Emscripten {expected} with emsdk_env.sh.") from error
        first_line = output.splitlines()[0] if output else ""
        match = re.search(r"\)\s+(\S+)", first_line)
        actual = match.group(1) if match else "unknown"
        if actual != expected:
            raise RuntimeError(
                f"{compiler} version mismatch: expected {expected}, found {actual}. "
                f"Run emsdk install {expected}, emsdk activate {expected}, then source emsdk_env.sh."
            )
    return expected


if __name__ == "__main__":
    try:
        print(validate_emscripten())
    except RuntimeError as error:
        raise SystemExit(str(error))
