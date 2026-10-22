"""Resolve and validate the repository-pinned Android NDK."""
import json
import os
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / ".android-ndk.json"


def pinned_ndk():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def resolve_ndk(sdk=None, environ=None):
    env = os.environ if environ is None else environ
    revision = pinned_ndk()["revision"]
    # 显式 SDK 参数优先；否则本地脚本和 CI 都先使用同一个 NDK 环境变量。
    root = None if sdk else env.get("ANDROID_NDK_ROOT") or env.get("ANDROID_NDK_HOME")
    if not root:
        sdk = sdk or env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT")
        if not sdk:
            raise RuntimeError("Set ANDROID_HOME or ANDROID_NDK_ROOT for the pinned NDK.")
        root = str(Path(sdk) / "ndk" / revision)
    root = Path(root).expanduser().resolve()
    props = root / "source.properties"
    if not props.is_file():
        raise RuntimeError(f"NDK {revision} is missing at {root}. Install with sdkmanager 'ndk;{revision}'.")
    values = dict(line.split("=", 1) for line in props.read_text().splitlines() if "=" in line)
    actual = next((v.strip() for k, v in values.items() if k.strip() == "Pkg.Revision"), "unknown")
    if actual != revision:
        raise RuntimeError(f"NDK version mismatch: expected {revision}, found {actual} at {root}.")
    return str(root)


if __name__ == "__main__":
    try:
        print(resolve_ndk())
    except RuntimeError as error:
        raise SystemExit(str(error))
