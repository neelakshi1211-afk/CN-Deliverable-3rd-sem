import json, tempfile, unittest
from pathlib import Path
from detector import detect_events, ConnectionRateDetector

class DetectorTests(unittest.TestCase):
    def test_alert_at_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"alerts.jsonl"
            events=[{"timestamp":100+i,"source":"10.0.0.1"} for i in range(5)]
            self.assertEqual(detect_events(events, 5, 10, out), 1)
            alert=json.loads(out.read_text().splitlines()[0])
            self.assertEqual(alert["event"], "HIGH_CONNECTION_RATE")
            self.assertEqual(alert["source"], "10.0.0.1")
    def test_no_alert_below_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"alerts.jsonl"
            events=[{"timestamp":100+i,"source":"10.0.0.2"} for i in range(2)]
            self.assertEqual(detect_events(events, 5, 10, out), 0)
            self.assertFalse(out.exists())
    def test_stateful_detector_alerts_across_separate_events(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "alerts.jsonl"
            detector = ConnectionRateDetector(3, 10, out)

            self.assertFalse(
                detector.process({"timestamp": 100, "source": "10.0.0.3"})
            )
            self.assertFalse(
                detector.process({"timestamp": 101, "source": "10.0.0.3"})
            )
            self.assertTrue(
                detector.process({"timestamp": 102, "source": "10.0.0.3"})
            )

            alert = json.loads(out.read_text().splitlines()[0])
            self.assertEqual(alert["source"], "10.0.0.3")
            self.assertEqual(alert["connection_count"], 3)

if __name__ == "__main__": unittest.main()
