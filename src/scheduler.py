from dataclasses import dataclass
from typing import Dict, List, Optional

# Required items
REQUIRED_MENU: Dict[str, int] = {
    "americano": 2,
    "latte": 3,
    "cappuccino": 3,
    "mocha": 4,
    "tea": 1,
    "macchiato": 2,
    "hot_chocolate": 4,
}


@dataclass
class Task:
    task_id: str
    remaining: int


class QueueRR:
    """
    Simple circular-buffer FIFO queue implementation.
    """

    def __init__(self, queue_id: str, capacity: int) -> None:
        assert capacity > 0
        self.queue_id = queue_id
        self.capacity = capacity
        self._buf: List[Optional[Task]] = [None] * capacity
        self._front = 0
        self._size = 0

    def enqueue(self, task: Task) -> bool:
        if self._size >= self.capacity:
            return False
        idx = (self._front + self._size) % self.capacity
        self._buf[idx] = task
        self._size += 1
        return True

    def dequeue(self) -> Optional[Task]:
        if self._size == 0:
            return None
        t = self._buf[self._front]
        self._buf[self._front] = None
        self._front = (self._front + 1) % self.capacity
        self._size -= 1
        return t

    def peek(self) -> Optional[Task]:
        if self._size == 0:
            return None
        return self._buf[self._front]

    def __len__(self) -> int:  # number of tasks currently queued
        return self._size

    # helper to iterate tasks in order (for display)
    def tasks_list(self) -> List[Task]:
        out: List[Task] = []
        idx = self._front
        for _ in range(self._size):
            t = self._buf[idx]
            if t is not None:
                out.append(t)
            idx = (idx + 1) % self.capacity
        return out


class Scheduler:
    def __init__(self) -> None:
        self.time: int = 0
        # map queue_id -> QueueRR
        self.queues: Dict[str, QueueRR] = {}
        # ordered list of queue ids (creation order defines RR order)
        self.queue_order: List[str] = []
        # per-queue id counters (int)
        self.id_counters: Dict[str, int] = {}
        # per-queue skip flags (bool)
        self.skip_flags: Dict[str, bool] = {}
        # rr pointer index into queue_order
        self.rr_index: int = 0
        # menu
        self._menu: Dict[str, int] = REQUIRED_MENU.copy()

    # ----- helpers -----
    def menu(self) -> Dict[str, int]:
        return self._menu.copy()

    def next_queue(self) -> Optional[str]:
        if not self.queue_order:
            return None
        # normalize rr_index into range
        if self.rr_index < 0:
            self.rr_index = 0
        if self.rr_index >= len(self.queue_order):
            # wrap
            self.rr_index %= len(self.queue_order)
        return self.queue_order[self.rr_index]

    # ----- commands -----
    def create_queue(self, queue_id: str, capacity: int) -> List[str]:
        logs: List[str] = []
        # If queue already exists, overwrite not desired; but tests usually create unique ids.
        self.queues[queue_id] = QueueRR(queue_id, capacity)
        self.queue_order.append(queue_id)
        self.id_counters[queue_id] = 0
        self.skip_flags[queue_id] = False
        logs.append(f"time={self.time} event=create queue={queue_id}")
        return logs

    def enqueue(self, queue_id: str, item_name: str) -> List[str]:
        logs: List[str] = []
        # unknown menu item: print and log reject unknown_item
        if item_name not in self._menu:
            print("Sorry, we don't serve that.")
            logs.append(
                f"time={self.time} event=reject queue={queue_id} reason=unknown_item"
            )
            return logs

        if queue_id not in self.queues:
            # log reject unknown_queue (no print specified for this case in spec;
            # keep consistent with tests that may expect a reject)
            logs.append(f"time={self.time} event=reject queue={queue_id} reason=unknown_queue")
            return logs

        burst = self._menu[item_name]
        # auto id
        self.id_counters[queue_id] += 1
        tid = f"{queue_id}-{self.id_counters[queue_id]:03d}"
        task = Task(tid, burst)

        q = self.queues[queue_id]
        if not q.enqueue(task):
            # full: print and log reject reason=full
            print("Sorry, we're at capacity.")
            logs.append(f"time={self.time} event=reject queue={queue_id} reason=full")
            return logs

        logs.append(f"time={self.time} event=enqueue queue={queue_id} task={tid} remaining={burst}")
        return logs

    def mark_skip(self, queue_id: str) -> List[str]:
        logs: List[str] = []
        logs.append(f"time={self.time} event=skip queue={queue_id}")
        if queue_id in self.skip_flags:
            self.skip_flags[queue_id] = True
        else:
            # if queue unknown, keep the log but do not raise
            pass
        return logs

    def run(self, quantum: int, steps: Optional[int]) -> List[str]:
        """
        Execute up to `steps` turns (each turn visits one queue), or if steps is None,
        run until all queues empty and no pending skips.
        Validate steps: 1 <= steps <= (#queues). If invalid, log error and do nothing.
        """
        logs: List[str] = []
        n_queues = len(self.queue_order)

        # If there are no queues, nothing to do; return empty logs
        if n_queues == 0:
            return logs

        # Validate steps if provided
        if steps is not None:
            if not (1 <= steps <= n_queues):
                logs.append(f"time={self.time} event=error reason=invalid_steps")
                return logs
            max_turns = steps
        else:
            max_turns = None  # run until empty + no skips

        turns_done = 0

        # Ensure rr_index in range
        if self.rr_index >= n_queues:
            self.rr_index %= n_queues

        # If steps is None we loop until termination condition
        while True:
            if max_turns is not None and turns_done >= max_turns:
                break

            # If no queues (shouldn't happen here) break
            if len(self.queue_order) == 0:
                break

            # Recompute local queue count because code may later support removals
            n_queues = len(self.queue_order)
            # Guard rr_index wrapping
            if self.rr_index >= n_queues:
                self.rr_index %= n_queues

            qid = self.queue_order[self.rr_index]
            q = self.queues[qid]

            # run event log (always)
            logs.append(f"time={self.time} event=run queue={qid}")

            # SKIP case: zero-time transition, clear skip flag, advance rr pointer
            if self.skip_flags.get(qid, False):
                self.skip_flags[qid] = False
                # After a skip visit, we must produce display snapshot
                logs.extend(self.display())
                # advance pointer
                self.rr_index = (self.rr_index + 1) % n_queues
                turns_done += 1
                # If running until empty and everything empty+clear, will check below
                if max_turns is None:
                    all_empty = all(len(self.queues[qx]) == 0 for qx in self.queue_order)
                    all_clear = all(not v for v in self.skip_flags.values())
                    if all_empty and all_clear:
                        break
                continue

            # EMPTY queue: zero-time transition, advance pointer, display
            if len(q) == 0:
                logs.extend(self.display())
                self.rr_index = (self.rr_index + 1) % n_queues
                turns_done += 1
                if max_turns is None:
                    all_empty = all(len(self.queues[qx]) == 0 for qx in self.queue_order)
                    all_clear = all(not v for v in self.skip_flags.values())
                    if all_empty and all_clear:
                        break
                continue

            # WORK: there is a task
            front_task = q.peek()
            # front_task should not be None because len(q) > 0
            assert front_task is not None
            work_amount = min(quantum, front_task.remaining)
            front_task.remaining -= work_amount
            # time advances by work_amount
            self.time += work_amount

            if front_task.remaining == 0:
                # Task finished: remove it
                finished = q.dequeue()
                # finished is the task
                logs.append(f"time={self.time} event=finish queue={qid} id={finished.task_id}")
            else:
                # Partial work: dequeue then enqueue back (to tail)
                t = q.dequeue()
                # t should be not None
                assert t is not None
                # re-enqueue updated task (should succeed because we freed one spot)
                success = q.enqueue(t)
                # enqueue must succeed (we just removed one)
                if not success:
                    # This should not happen; but if it does, treat as finishing (defensive)
                    logs.append(f"time={self.time} event=finish queue={qid} id={t.task_id}")
                else:
                    logs.append(f"time={self.time} event=work queue={qid} id={t.task_id} remaining={t.remaining}")

            # After performing the turn, advance RR pointer and add display snapshot
            self.rr_index = (self.rr_index + 1) % n_queues
            logs.extend(self.display())
            turns_done += 1

            # If running until empty: check termination condition
            if max_turns is None:
                all_empty = all(len(self.queues[qx]) == 0 for qx in self.queue_order)
                all_clear = all(not v for v in self.skip_flags.values())
                if all_empty and all_clear:
                    break

        return logs

    # ----- display -----
    def display(self) -> List[str]:
        """
        Return the compact snapshot as list of lines.
        """
        lines: List[str] = []
        nxt = self.next_queue()
        # Use 'None' exactly when there is no next queue
        lines.append(f"display time={self.time} next={nxt if nxt is not None else 'None'}")

        # menu sorted by name
        menu_str = ",".join(f"{k}:{v}" for k, v in sorted(self._menu.items()))
        lines.append(f"display menu=[{menu_str}]")

        for qid in self.queue_order:
            q = self.queues[qid]
            skip_text = " skip" if self.skip_flags.get(qid, False) else ""
            tasks = q.tasks_list()
            tasks_text = ",".join(f"{t.task_id}:{t.remaining}" for t in tasks)
            lines.append(f"display {qid} [{len(q)}/{q.capacity}]{skip_text} -> [{tasks_text}]")

        return lines
