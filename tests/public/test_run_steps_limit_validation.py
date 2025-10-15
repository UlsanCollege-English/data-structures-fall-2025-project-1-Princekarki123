import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from scheduler import Scheduler

def test_steps_cannot_exceed_number_of_queues():
    s = Scheduler()
    s.create_queue("Only", 1)

    out = s.run(quantum=1, steps=2)  # exceeds #queues (=1)
    assert any("event=error" in l and "invalid_steps" in l for l in out)

def test_steps_must_be_at_least_one():
    s = Scheduler()
    s.create_queue("A", 1)
    out = s.run(quantum=1, steps=0)
    assert any("event=error" in l and "invalid_steps" in l for l in out)
