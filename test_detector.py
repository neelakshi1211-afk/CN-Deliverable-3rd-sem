import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"person3_monitor_detection"))
from detector import detect
class Tests(unittest.TestCase):
    def test_threshold_alert(self):
        ev=[{"source":"10.0.0.1","timestamp":i} for i in range(1,4)]
        self.assertEqual(detect(ev,3,10)[0]["source"],"10.0.0.1")
    def test_below_threshold(self):
        ev=[{"source":"10.0.0.1","timestamp":i} for i in range(1,3)]
        self.assertEqual(detect(ev,3,10),[])
    def test_old_events_expire(self):
        ev=[{"source":"10.0.0.1","timestamp":t} for t in (1,2,30)]
        self.assertEqual(detect(ev,3,10),[])
if __name__=="__main__": unittest.main()
