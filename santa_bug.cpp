/*
    Compile with:
      clang++ -std=c++20 -stdlib=libc++ -o santa santa_bug.cpp
    or
      g++ -std=c++20 -o santa santa_bug.cpp
*/

#include <iostream>
#include <thread>
#include <semaphore>
#include <mutex>
#include <chrono>
#include <vector>
#include <random>

//
// ------------------------------------------------------------
// Configuration
// ------------------------------------------------------------
constexpr int NUM_REINDEER = 9;
constexpr int NUM_ELVES    = 10;   // total elves in the system
constexpr int GROUP_SIZE   = 3;    // exactly 3 elves must arrive to wake Santa

// How many times do we let each thread "work" or "vacation"
constexpr int ELF_WORK_ROUNDS          = 3;
constexpr int REINDEER_VACATION_ROUNDS = 2;

constexpr double SLOWDOWN_FACTOR = 10.0;

//
// ------------------------------------------------------------
// Shared State
// ------------------------------------------------------------

// For reindeer
int reindeerCount = 0;  
// For elves
int elfCount = 0;       

// Guard both counters with a mutex
std::mutex mtx;

// ------------------------------------------------------------
// Semaphores for synchronization
// ------------------------------------------------------------

// Santa sleeps on this until 9 reindeer or 3 elves are ready
static std::counting_semaphore<9999> santaSem(0);

// Reindeer wait on this until Santa is ready to harness them
static std::counting_semaphore<9999> reindeerSem(0);

// Elves: allow up to 3 “in flight” to form a group
static std::counting_semaphore<9999> onlyElves(3);

// The 1st and 2nd elves in a group wait on this (the 3rd wakes Santa)
static std::counting_semaphore<9999> santaSignal(0);

// The “problem” semaphore: Santa signals it 3 times when he’s ready
static std::counting_semaphore<9999> problem(0);

// The “elfDone” semaphore: Santa signals 3 times after he’s answered them
static std::counting_semaphore<9999> elfDone(0);

// Just needed to prevent output getting jumbled
static std::mutex printMutex;

// ------------------------------------------------------------
// Utility: safe print
// ------------------------------------------------------------
void safePrint(const std::string &msg)
{
    std::lock_guard<std::mutex> lock(printMutex);
    std::cout << msg << std::endl;

    // Add a half-second pause after every printed line:
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
}

// ------------------------------------------------------------
// Utility: random sleep for demonstration
// ------------------------------------------------------------
void randomSleep(int minMs, int maxMs, double scale = 1.0)
{
    // Each thread has its own RNG
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<> dist(minMs, maxMs);
    auto ms = static_cast<int>(dist(rng) * scale);
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

// ------------------------------------------------------------
// Santa Thread
// ------------------------------------------------------------
void santaThread()
{
    safePrint("[Santa] Ho-ho-ho, I'm here...");
    for (;;)
    {
        // Wait until awakened by either all 9 reindeer or 3 elves
        santaSem.acquire();

        // Check who woke me
        std::unique_lock<std::mutex> lock(mtx);
        if (reindeerCount == NUM_REINDEER)
        {
            // All reindeer arrived
            safePrint("[Santa] All reindeer have arrived! Preparing the sleigh...");
            reindeerCount = 0;    // reset the count

            // Let each reindeer proceed
            for (int i = 0; i < NUM_REINDEER; i++) {
                reindeerSem.release();
            }

            lock.unlock();
            // Simulate delivering
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
            lock.lock();

            safePrint("[Santa] Done delivering toys; back to sleep!");
        }
        else if (elfCount == 3)
        {
            // 3 elves arrived (the 3rd elf woke Santa)
            safePrint("[Santa] 3 elves need help. Letting them in...");

            // Release the first 2 elves that were waiting on santaSignal
            for (int i = 0; i < (GROUP_SIZE - 1); i++) {
                santaSignal.release();
            }

            // Reset the elfCount while locked
            elfCount = 0;

            // Let all 3 elves ask their questions
            for (int i = 0; i < GROUP_SIZE; i++) {
                problem.release();
            }

            // Help them (simulate)
            lock.unlock();
            std::this_thread::sleep_for(std::chrono::milliseconds(700));
            lock.lock();

            safePrint("[Santa] Done helping these elves!");

            // Let the 3 elves know Santa’s done
            for (int i = 0; i < GROUP_SIZE; i++) {
                elfDone.release();
            }
        }
        else
        {
            // Possibly a spurious wakeup or partial group
            safePrint("[Santa] Woke up, but ReindeerCount=" 
                      + std::to_string(reindeerCount) + ", ElfCount=" + std::to_string(elfCount));
        }
    }
}

// ------------------------------------------------------------
// Reindeer Thread
// ------------------------------------------------------------
void reindeerThread(int id)
{
    for (int round = 0; round < REINDEER_VACATION_ROUNDS; round++)
    {
        // Vacation
        randomSleep(500, 1000, SLOWDOWN_FACTOR);
        {
            // Lock to safely increment
            std::unique_lock<std::mutex> lock(mtx);
            reindeerCount++;
            safePrint("[Reindeer " + std::to_string(id) + "] Returned. ReindeerCount=" + std::to_string(reindeerCount));

            // If this is the 9th reindeer, wake Santa
            if (reindeerCount == NUM_REINDEER) {
                safePrint("[Reindeer " + std::to_string(id) + "] I'm the last! Waking Santa!");
                santaSem.release();
            }
        }
        // Wait until Santa harnesses us
        reindeerSem.acquire(); // <- Bug right here - what if this is called after santa is releasing the reindeer?

        // Deliver toys
        safePrint("[Reindeer " + std::to_string(id) + "] Delivering toys...");
        randomSleep(300, 600, SLOWDOWN_FACTOR);
        safePrint("[Reindeer " + std::to_string(id) + "] Going back on vacation...");
    }
    safePrint("[Reindeer " + std::to_string(id) + "] Done, exiting thread.");
}

// ------------------------------------------------------------
// Elf Thread
// ------------------------------------------------------------
void elfThread(int id)
{
    for (int round = 0; round < ELF_WORK_ROUNDS; round++)
    {
        // Simulate working
        safePrint("[Elf " + std::to_string(id) + "] Making toys...");
        randomSleep(300, 600, SLOWDOWN_FACTOR);

        // 30% chance something goes wrong
        bool hasProblem = (rand() % 100 < 30);
        if (!hasProblem)
            continue;

        // Acquire a slot so only up to 3 elves can proceed
        onlyElves.acquire();

        {
            // Lock to safely increment
            std::unique_lock<std::mutex> lock(mtx);
            elfCount++;
            safePrint("[Elf " + std::to_string(id) + "] Has a problem! ElfCount=" + std::to_string(elfCount));

            if (elfCount == GROUP_SIZE)
            {
                safePrint("[Elf " + std::to_string(id) + "] I'm the 3rd elf, waking Santa!");
                santaSem.release();
            }
            else
            {
                // If not 3rd, wait outside
                safePrint("[Elf " + std::to_string(id) + "] Waiting outside for group of 3...");
            }
        }

        // If I'm NOT the 3rd, I block on santaSignal
        if (elfCount < GROUP_SIZE) {
            santaSignal.acquire();
        }

        // Wait for Santa to say "go ahead" (problem)
        problem.acquire();

        // Now talk to Santa
        safePrint("[Elf " + std::to_string(id) + "] Asking Santa my question...");
        randomSleep(200, 400, SLOWDOWN_FACTOR);

        // Wait until Santa's done helping
        elfDone.acquire();

        safePrint("[Elf " + std::to_string(id) + "] Done with Santa. Returning to work.");

        // Release slot so next elf can form a group
        onlyElves.release();
    }
    safePrint("[Elf " + std::to_string(id) + "] Done with all rounds, exiting.");
}

// ------------------------------------------------------------
// main()
// ------------------------------------------------------------
int main()
{
    srand((unsigned int)time(nullptr));

    // Start Santa
    std::thread santa(santaThread);

    // Start Reindeer
    std::vector<std::thread> reindeers;
    reindeers.reserve(NUM_REINDEER);
    for (int i = 1; i <= NUM_REINDEER; i++) {
        reindeers.emplace_back(reindeerThread, i);
    }

    // Start Elves
    std::vector<std::thread> elves;
    elves.reserve(NUM_ELVES);
    for (int i = 1; i <= NUM_ELVES; i++) {
        elves.emplace_back(elfThread, i);
    }

    // Join reindeer
    for (auto &r : reindeers) {
        r.join();
    }

    // Join elves
    for (auto &e : elves) {
        e.join();
    }

    // Santa runs forever in this demo, so detach or kill:
    santa.detach();

    safePrint("[Main] All reindeer and elves finished. Santa still dozing.");
    return 0;
}
