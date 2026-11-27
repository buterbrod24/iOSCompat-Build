import unittest
from metadata_request_model import Request,State,assess_response

class Tests(unittest.TestCase):
    def test_roundtrip(self):
        for state in State:
            for nonblocking in (True,False):
                r=Request(state,nonblocking)
                self.assertEqual(Request.decode(r.encode()),r)
    def test_zero(self):
        self.assertEqual(Request.decode(0),Request(State.COMPLETE,False))
    def test_nonblocking_bit(self):
        self.assertEqual(Request(State.LAYOUT_COMPLETE,True).encode(),0x13f)
    def test_order(self):
        states=list(State)
        for i,observed in enumerate(states):
            for j,required in enumerate(states):
                self.assertEqual(Request(required).satisfied_by(observed),i<=j)
    def test_invalid(self):
        for value in (-1,512,2,0xfe,True,"0"):
            with self.assertRaises(ValueError):Request.decode(value)
    def test_response(self):
        self.assertEqual(assess_response(Request(State.COMPLETE),State.COMPLETE),"satisfied")
        self.assertEqual(assess_response(Request(State.COMPLETE,True),State.ABSTRACT),"incomplete_nonblocking")
        self.assertEqual(assess_response(Request(State.COMPLETE),State.ABSTRACT),"inconsistent_blocking_observation")
    def test_no_unknown_observation(self):
        with self.assertRaises(ValueError):Request(State.COMPLETE).satisfied_by(0)
if __name__=="__main__":unittest.main()
