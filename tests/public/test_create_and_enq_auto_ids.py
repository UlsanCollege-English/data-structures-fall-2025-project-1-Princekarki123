import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from scheduler import Scheduler

def test_auto_task_ids_increment_per_queue():
    s = Scheduler()
    logs = s.create_queue("Mobile", 2)
    assert any("event=create queue=Mobile" in x for x in logs)

    logs = s.enqueue("Mobile", "latte")
    assert any("event=enqueue" in x and "task=Mobile-001" in x for x in logs)

    logs = s.enqueue("Mobile", "tea")
    assert any("event=enqueue" in x and "task=Mobile-002" in x for x in logs)
