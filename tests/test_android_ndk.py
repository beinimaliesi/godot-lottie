"""NDK pin resolution must be independent of unrelated SDK environment values."""
import runpy
import tempfile
import unittest
from pathlib import Path

TOOLS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/android_ndk.py"))


class AndroidNdkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.sdk = self.base / "sdk"
        self.good = self.sdk / "ndk" / TOOLS["pinned_ndk"]()["revision"]
        self.bad = self.base / "other-ndk"
        for directory, revision in ((self.good, TOOLS["pinned_ndk"]()["revision"]), (self.bad, "0.0.0")):
            directory.mkdir(parents=True)
            (directory / "source.properties").write_text("Pkg.Revision = " + revision + "\n")

    def test_sdk_fallback(self):
        for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
            self.assertEqual(TOOLS["resolve_ndk"](environ={name: str(self.sdk)}), str(self.good))

    def test_explicit_ndk_overrides_environment_sdk(self):
        for name in ("ANDROID_NDK_ROOT", "ANDROID_NDK_HOME"):
            self.assertEqual(TOOLS["resolve_ndk"](environ={name: str(self.good), "ANDROID_HOME": "/invalid"}), str(self.good))

    def test_command_line_sdk_overrides_environment(self):
        self.assertEqual(TOOLS["resolve_ndk"](sdk=str(self.sdk), environ={"ANDROID_NDK_ROOT": str(self.bad)}), str(self.good))

    def test_mismatched_ndk_does_not_fall_back(self):
        with self.assertRaisesRegex(RuntimeError, "version mismatch"):
            TOOLS["resolve_ndk"](environ={"ANDROID_NDK_ROOT": str(self.bad), "ANDROID_HOME": str(self.sdk)})

    def test_missing_installation(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            TOOLS["resolve_ndk"](environ={"ANDROID_HOME": str(self.base / "missing")})

    def test_missing_environment(self):
        with self.assertRaisesRegex(RuntimeError, "Set ANDROID_HOME"):
            TOOLS["resolve_ndk"](environ={})


if __name__ == "__main__":
    unittest.main()
