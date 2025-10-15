[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/JWEh_q2R)
# Multi-Queue Round-Robin Café (Interactive CLI)

## How to run
1. Make sure these three files are in the same folder:
   - scheduler.py  
   - parser.py  
   - cli.py  

2. Open the terminal in that folder and run:


## How to run tests locally
If you want to test your code, run this in the terminal:
pytest

Or if you have a file with commands (for example, `sample_input.txt`), run:



## Complexity Notes
Briefly justify:

- Queue Design:
I used a circular buffer for the queue.
It stores items in a fixed-size list and moves the front and rear using modular arithmetic.
This makes adding and removing tasks very fast and does not use deque or queue.Queue.

Time Complexity:

enqueue → O(1)

dequeue → O(1)

run → O(number of turns + total work time)

Space Complexity:

O(N) where N is the total number of tasks plus small extra data.
