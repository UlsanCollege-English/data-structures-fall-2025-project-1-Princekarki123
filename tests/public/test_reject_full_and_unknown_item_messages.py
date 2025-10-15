import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from scheduler import Scheduler

def test_unknown_item_reject_and_message(capsys):
    s = Scheduler()
    s.create_queue("WalkIns", 2)

    logs = s.enqueue("WalkIns", "cortado")  # not on menu
    out, _ = capsys.readouterr()
    assert "Sorry, we don't serve that." in out
    assert any("event=reject" in l and "reason=unknown_item" in l for l in logs)

def test_full_queue_reject_and_message(capsys):
    s = Scheduler()
    s.create_queue("WalkIns", 1)
    s.enqueue("WalkIns", "latte")  # fills capacity

    logs = s.enqueue("WalkIns", "tea")  # should reject
    out, _ = capsys.readouterr()
    assert "Sorry, we're at capacity." in out
    assert any("event=reject" in l and "reason=full" in l for l in logs)
