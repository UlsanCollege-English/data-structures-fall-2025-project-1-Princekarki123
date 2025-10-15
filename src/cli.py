import sys
from typing import List
from parser import parse_command
from scheduler import Scheduler


def main() -> None:
    sched = Scheduler()

    for raw in sys.stdin:
        line = raw.rstrip("\n")

        # Blank line ends session
        if line == "":
            print("Break time!")
            return

        parsed = parse_command(line)
        logs: List[str] = []

        if parsed is None:
            # comment or whitespace-only line inside session: ignore
            pass
        else:
            cmd, args = parsed
            try:
                if cmd == "CREATE":
                    if len(args) != 2:
                        logs.append(f"time=? event=error reason=bad_args")
                    else:
                        qid, cap_str = args
                        try:
                            cap = int(cap_str)
                        except ValueError:
                            raise ValueError("bad_args")
                        logs.extend(sched.create_queue(qid, cap))

                elif cmd == "ENQ":
                    if len(args) != 2:
                        logs.append(f"time=? event=error reason=bad_args")
                    else:
                        qid, item = args
                        logs.extend(sched.enqueue(qid, item))

                elif cmd == "SKIP":
                    if len(args) != 1:
                        logs.append(f"time=? event=error reason=bad_args")
                    else:
                        (qid,) = args
                        logs.extend(sched.mark_skip(qid))

                elif cmd == "RUN":
                    if not (1 <= len(args) <= 2):
                        logs.append(f"time=? event=error reason=bad_args")
                    else:
                        # parse quantum and optionally steps
                        quantum = int(args[0])
                        steps = int(args[1]) if len(args) == 2 else None
                        logs.extend(sched.run(quantum, steps))

                else:
                    logs.append(f"time=? event=error reason=unknown_command")

            except ValueError:
                logs.append(f"time=? event=error reason=bad_args")

        # Print logs produced by this input line (if any)
        if logs:
            print("\n".join(logs))


if __name__ == "__main__":
    main()
