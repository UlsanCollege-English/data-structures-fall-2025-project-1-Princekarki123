import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from scheduler import Scheduler

def test_large_mixed_sequence_deterministic():
    s = Scheduler()
    s.create_queue("Mobile", 3)
    s.create_queue("WalkIns", 3)
    s.create_queue("Faculty", 2)

    # Seed some items
    s.enqueue("Mobile",  "americano")   # 2
    s.enqueue("WalkIns", "latte")       # 3
    s.enqueue("Faculty", "tea")         # 1
    s.enqueue("WalkIns", "mocha")       # 4
    s.enqueue("Mobile",  "macchiato")   # 2

    # First round of turns (max steps == #queues == 3)
    logs1 = s.run(quantum=1, steps=3)
    # Second round
    logs2 = s.run(quantum=2, steps=3)

    # Sanity checks on shape:
    all_logs = logs1 + logs2
    # Should have exactly 6 run events (3 + 3)
    assert sum(1 for l in all_logs if "event=run" in l) == 6
    # There should be some work and possibly finishes
    assert any("event=work" in l for l in all_logs)
    assert any("event=finish" in l for l in all_logs)
