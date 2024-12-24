/*
    Santa Claus Problem (C++20 semaphores, bug fixed)

    Compile with:
      clang++ -std=c++20 -stdlib=libc++ -o santa santa_complex.cpp
    or
      g++ -std=c++20 -o santa santa_complex.cpp
*/

#include <iostream>
#include <thread>
#include <semaphore>
#include <vector>
#include <atomic>
#include <mutex>
#include <chrono>
#include <cstdlib>
#include <ctime>

// -----------------------------------------
// Global parameters
// -----------------------------------------
static const int NUM_REINDEER = 9;
static const int NUM_ELVES    = 10;

// -----------------------------------------
// Shared state + synchronization
// -----------------------------------------
std::binary_semaphore santaSem(0);     // Santa sleeps until awakened
std::binary_semaphore reindeerSem(0);  // Reindeer wait on this to be harnessed
std::binary_semaphore elfSem(0);       // Elves wait on this to enter for help
std::binary_semaphore mutexSem(1);     // Lock for shared data updates

// Because semaphores alone do not carry “conditions,”
// we keep some shared counters/flags:
int reindeerCount = 0;
int elfCount      = 0;

// Keep track of whether reindeer have priority
// or a group of 3 elves is waiting:
bool reindeerReady = false;
bool elvesReady    = false;

// Utility: random small delay
void randomDelay(int maxMs = 300)
{
    int ms = rand() % maxMs;
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

// -----------------------------------------
// Reindeer Thread
// -----------------------------------------
void reindeerFunc(int id)
{
    {
        // Print once, on vacation
        std::cout << "[Reindeer " << id << "] On vacation...\n";
    }
    randomDelay(300);  // Simulate vacation

    // Return from vacation
    mutexSem.acquire();
    reindeerCount++;
    std::cout << "[Reindeer " << id << "] Returned. ReindeerCount=" 
              << reindeerCount << "\n";

    if (reindeerCount == NUM_REINDEER) {
        // last reindeer => set reindeerReady = true
        reindeerReady = true;
        std::cout << "[Santa] All reindeer have arrived! Preparing the sleigh...\n";
        // Wake Santa (only once)
        santaSem.release();
    }
    mutexSem.release();

    // Wait until Santa harnesses us => “deliver toys”
    // We must not assume the next thing after .release() is immediate harness:
    // so we wait on reindeerSem, but also re-check the condition in a while loop:
    bool delivered = false;
    while (!delivered) {
        reindeerSem.acquire();  // Wait for Santa to release us
        // Now we check if Santa truly harnessed (reindeerCount reset to 0).
        // If not harnessed, we re-acquire.
        mutexSem.acquire();
        if (reindeerCount == 0) {
            // Santa harnessed the reindeer => proceed to deliver
            std::cout << "[Reindeer " << id << "] Delivering toys\n";
            delivered = true;
        } else {
            // Oops, we got awakened but Santa might have signaled
            // only part of the reindeer, or we got "extra" release
            // => go back to waiting
        }
        mutexSem.release();
    }

    // Done delivering
    randomDelay(150);
    // Going back on vacation
    std::cout << "[Reindeer " << id << "] Going back on vacation...\n";
}

// -----------------------------------------
// Elf Thread
// -----------------------------------------
void elfFunc(int id)
{
    randomDelay(400);  // Doing some work, then we get stuck

    // Need to ask Santa
    mutexSem.acquire();
    elfCount++;
    std::cout << "[Elf " << id << "] Has a problem! ElfCount=" 
              << elfCount << "\n";
    if (elfCount == 3) {
        elvesReady = true;
        std::cout << "[Santa] 3 elves need help. Letting them in...\n";
        // Wake Santa
        santaSem.release();
    }
    mutexSem.release();

    // Wait for Santa to finish helping
    // Similar pattern: we keep waiting on elfSem, but do a check:
    bool helped = false;
    while (!helped) {
        elfSem.acquire();
        // Check if Santa has finished helping
        mutexSem.acquire();
        // If elfCount = 0, that means Santa is done with the current group
        if (elfCount == 0) {
            std::cout << "[Elf " << id << "] Back to making toys!\n";
            helped = true;
        }
        mutexSem.release();
    }
}

// -----------------------------------------
// Santa Thread
// -----------------------------------------
void santaFunc()
{
    while (true) {
        // Santa sleeps until awakened by either reindeerReady or elvesReady
        santaSem.acquire();  // Wait for a wake-up
        // Check who woke me. Reindeer or a group of 3 elves?

        // Priority: handle reindeer first if reindeerReady == true
        mutexSem.acquire();
        if (reindeerReady) {
            // All reindeer are here => harness them => deliver toys
            // Indicate we’re about to harness them:
            reindeerCount = 0;  // means harnessed
            std::cout << "[Santa] Done delivering toys; back to sleep!\n";

            // Release *all* reindeer (9 times). They’ll see reindeerCount=0
            for (int i = 0; i < NUM_REINDEER; i++) {
                reindeerSem.release();
            }
            reindeerReady = false;  // done
            mutexSem.release();
        } 
        else if (elvesReady) {
            // Help 3 elves
            std::cout << "[Santa] Done helping these elves!\n";
            // Reset elfCount => done with the group
            elfCount = 0;

            // Release exactly 3 elves. They will see elfCount=0 => done
            for (int i = 0; i < 3; i++) {
                elfSem.release();
            }
            elvesReady = false;
            mutexSem.release();
        }
        else {
            // Possibly a “spurious” wake-up. This is much rarer with semaphores,
            // but let's handle it: just release the mutex and go back to sleep.
            mutexSem.release();
        }
        // Then Santa loops back to sleep
    }
}

// -----------------------------------------
// main()
// -----------------------------------------
int main()
{
    srand(static_cast<unsigned>(time(nullptr)));

    // Start Santa
    std::thread santaThr(santaFunc);

    // Start Reindeer
    std::vector<std::thread> reindeers;
    reindeers.reserve(NUM_REINDEER);
    for (int i = 1; i <= NUM_REINDEER; i++) {
        reindeers.emplace_back(std::thread(reindeerFunc, i));
    }

    // Start Elves
    std::vector<std::thread> elves;
    elves.reserve(NUM_ELVES);
    for (int i = 1; i <= NUM_ELVES; i++) {
        elves.emplace_back(std::thread(elfFunc, i));
    }

    // Join reindeers and elves
    for (auto &r : reindeers) {
        r.join();
    }
    for (auto &e : elves) {
        e.join();
    }

    // For a real system, we’d have a more graceful shutdown for Santa.
    // For demonstration, forcibly detach or kill Santa's infinite loop:
    santaThr.detach();

    std::cout << "[Info] All threads (except Santa) have finished.\n";
    return 0;
}
