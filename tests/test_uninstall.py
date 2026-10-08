"""
Tests for jamovi-antigravity uninstaller
"""

import os
import sys
import unittest
import tempfile
import subprocess
import shutil

class TestUninstaller(unittest.TestCase):
    def test_dry_run_flag(self):
        script_path = os.path.join(os.path.dirname(__file__), "..", "uninstall.sh")
        res = subprocess.run([script_path, "--test"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("[TEST MODE]", res.stdout)
        self.assertIn("Verification passed", res.stdout)

    def test_mock_environment_teardown(self):
        # Create a mock home directory
        mock_home = tempfile.mkdtemp(prefix="mock_home_")
        mock_mcp = os.path.join(mock_home, ".gemini", "antigravity", "mcp", "jamovi")
        mock_agent = os.path.join(mock_home, ".gemini", "config", "agents", "jamovi-analyst.md")

        os.makedirs(mock_mcp, exist_ok=True)
        os.makedirs(os.path.dirname(mock_agent), exist_ok=True)

        with open(os.path.join(mock_mcp, "server.py"), "w") as f:
            f.write("# dummy server")
        with open(mock_agent, "w") as f:
            f.write("# dummy agent")

        self.assertTrue(os.path.exists(mock_mcp))
        self.assertTrue(os.path.exists(mock_agent))

        # Run uninstall script with HOME overridden
        script_path = os.path.join(os.path.dirname(__file__), "..", "uninstall.sh")
        env = os.environ.copy()
        env["HOME"] = mock_home

        res = subprocess.run([script_path], env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

        # Assert mock directories were removed
        self.assertFalse(os.path.exists(mock_mcp))
        self.assertFalse(os.path.exists(mock_agent))

        shutil.rmtree(mock_home, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
