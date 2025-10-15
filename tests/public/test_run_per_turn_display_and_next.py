import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))
from scheduler import Scheduler

def _has_run_on_queue(logs, qid):
    return any(f"event=run queue={qid}" in l for l in logs)

def test_run_two_turns_and_progress_time():
    s = Scheduler()
    s.create_queue("Mobile", 2)
    s.create_queue("Faculty", 2)

    s.enqueue("Mobile", "tea")       # 1 min
    s.enqueue("Faculty", "latte")    # 3 min

    # steps must be ≤ #queues == 2
    logs = s.run(quantum=1, steps=2)

    # Two turns visited; both should produce a run event
    assert sum(1 for l in logs if "event=run" in l) == 2
    # Work must happen on both queues across these two turns
    assert _has_run_on_queue(logs, "Mobile")
    assert _has_run_on_queue(logs, "Faculty")

    # There should be at least one work/finish line in total
    assert any("event=work" in l or "event=finish" in l for l in logs)

