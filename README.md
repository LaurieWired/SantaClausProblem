# Santa Claus Problem :santa:

This repository demonstrates the classic concurrency puzzle known as the Santa Claus Problem, originally described by John Trono. The problem requires synchronizing Santa, nine Reindeer returning from vacation, and a group of Elves needing Santa's help — ensuring that Santa only wakes up under the proper conditions. It highlights important concurrency concepts like resource sharing, scheduling, and synchronization constraints.

https://github.com/user-attachments/assets/64a56c01-f7bf-40cc-b5da-e81018c3439b

## What's in this repo? :mag_right:

1. **C++ Code**  
   - Provides two versions of the Santa Claus solution:
     - [santa_bug.cpp](https://github.com/LaurieWired/SantaClausProblem/blob/main/santa_bug.cpp) - The original approach (contains a known scheduling assumption bug).
     - [santa.cpp](https://github.com/LaurieWired/SantaClausProblem/blob/main/santa.cpp) - A fixed solution properly handling the bug.

2. **Python Visualization**  
   - A Tkinter-based GUI that launches the C++ program in the background and animates Santa, Reindeer, and Elves.
   - Displays concurrency events, reindeer arrivals, and elves' help requests in an interactive way.

## Quick Start :runner:

### 1. Compile the C++ code
```bash
g++ -std=c++20 santa.cpp -o santa
```

### 2. Run the Python GUI
```bash
python3 santa_ui.py
```

## Why Does This Matter? :thinking:

- **Concurrency**: The Santa Claus Problem illustrates how multiple threads (or processes) can coordinate access to shared resources and synchronization primitives.
- **Scheduling Pitfalls**: The classic solution can fail if threads are not scheduled as assumed. This repo showcases both the original approach and the improved fix.
- **Real-World Relevance**: Understanding concurrency is essential for designing reliable, multi-threaded applications.
