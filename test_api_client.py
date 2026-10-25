import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CliTests(unittest.TestCase):
    def test_help(self):
        result = subprocess.run([sys.executable, str(ROOT / 'api_client.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('block', result.stdout)

    def test_missing_ip(self):
        result = subprocess.run([sys.executable, str(ROOT / 'api_client.py'), 'block'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--ip is required', result.stderr)

if __name__ == '__main__':
    unittest.main()
