"""
/************************************************
 CS 440 Operating Systems
 Project 3 CPU Scheduling Simulation
 Names: Augustus Allred, David Gonzalez
 Date: 3/13/2026
************************************************/
"""

from dataclasses import dataclass, field
import copy
import random


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    remaining: int = field(init=False)
    first_start = None
    completion = None

    def __post_init__(self):
        self.remaining = self.burst


def clone_processes(processes):
    return copy.deepcopy(processes)


def sort_by_pid(processes):
    return sorted(processes, key=lambda p: int(p.pid[1:]))


def get_ready_processes(processes, current_time):
    return [p for p in processes if p.arrival <= current_time and p.remaining > 0]


def get_next_arrival_time(processes, current_time):
    future = [p.arrival for p in processes if p.arrival > current_time and p.remaining > 0]
    return min(future) if future else None


def all_complete(processes):
    return all(p.remaining == 0 for p in processes)


def start_process(process, current_time):
    # Response time depends on the first time a process gets the CPU.
    if process.first_start is None:
        process.first_start = current_time


def run_for(process, amount, current_time):
    # Shared run helper so every algorithm updates timing fields the same way.
    start_process(process, current_time)
    process.remaining -= amount
    end_time = current_time + amount

    if process.remaining == 0:
        process.completion = end_time

    return end_time


# Calculates average waiting time and response time for all processes.
# waiting = completion - arrival - burst
# response = first time CPU runs - arrival
def compute_metrics(processes):
    total_wait = 0
    total_response = 0

    for p in processes:
        response = p.first_start - p.arrival
        waiting = p.completion - p.arrival - p.burst
        total_response += response
        total_wait += waiting

    avg_wait = total_wait / len(processes)
    avg_response = total_response / len(processes)
    return avg_wait, avg_response


def make_result(name, processes, trace):
    # Standard result structure so every scheduling algorithm returns the same data
    avg_wait, avg_response = compute_metrics(processes)
    completion_time = max(p.completion for p in processes)

    return {
        "name": name,
        "trace": trace,
        "completion_time": completion_time,
        "avg_wait": avg_wait,
        "avg_response": avg_response,
        "processes": processes
    }


def compute_checksum(results):
    total_completion = 0
    total_wait100 = 0
    total_resp100 = 0

    for result in results:
        total_completion += result["completion_time"]
        total_wait100 += round(result["avg_wait"] * 100)
        total_resp100 += round(result["avg_response"] * 100)

    return total_completion + total_wait100 + total_resp100


def print_process_table(processes):
    print("Generated process table:")
    for p in sort_by_pid(processes):
        print(f"{p.pid}: arrival={p.arrival}, burst={p.burst}")


def print_algorithm_result(result):
    print(f"\n{result['name']} Trace:")
    for line in result["trace"]:
        print(line)

    print(f"Completed in {result['completion_time']} cycles.")
    print(f"Avg wait = {result['avg_wait']:.2f}")
    print(f"Avg response = {result['avg_response']:.2f}")


def print_checksum(results):
    print(f"\nCHECKSUM: {compute_checksum(results)}")


# Scheduling algorithms
def fcfs(processes, latency):
    procs = clone_processes(processes)
    trace = []
    time = 0
    first_dispatch = True

    while not all_complete(procs):
        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.arrival, int(p.pid[1:]))
        )

        if not ready:
            time = get_next_arrival_time(procs, time)
            continue

        current = ready[0]

        if not first_dispatch:
            trace.append(f"@t={time}, context switch {latency} occurs")
            time += latency

        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)
        first_dispatch = False

    trace.append(f"@t={time}, all processes complete")
    return make_result("FCFS", procs, trace)


def sjf(processes, latency):
    procs = clone_processes(processes)
    trace = []
    time = 0
    first_dispatch = True

    while not all_complete(procs):
        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.burst, p.arrival, int(p.pid[1:]))
        )

        if not ready:
            time = get_next_arrival_time(procs, time)
            continue

        current = ready[0]

        if not first_dispatch:
            trace.append(f"@t={time}, context switch {latency} occurs")
            time += latency

        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)
        first_dispatch = False

    trace.append(f"@t={time}, all processes complete")
    return make_result("SJF", procs, trace)


def srtf(processes, latency):
    raise NotImplementedError("SRTF scheduling not implemented yet.")


def rr(processes, quantum, latency):
    raise NotImplementedError("Round Robin scheduling not implemented yet.")


def random_selection(processes, latency, rng):
    procs = clone_processes(processes)
    trace = []
    time = 0
    first_dispatch = True

    while not all_complete(procs):
        ready = get_ready_processes(procs, time)

        if not ready:
            time = get_next_arrival_time(procs, time)
            continue

        current = rng.choice(ready)

        if not first_dispatch:
            trace.append(f"@t={time}, context switch {latency} occurs")
            time += latency

        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)
        first_dispatch = False

    trace.append(f"@t={time}, all processes complete")
    return make_result("Random", procs, trace)


def main():
    processes = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 6)
    ]

    latency = 1

    print_process_table(processes)

    for seed in [1, 2, 3, 4, 5, 6, 7, 8]:
        rng = random.Random(seed)
        result = random_selection(processes, latency, rng)
        print(f"\nSeed = {seed}")
        print_algorithm_result(result)

    print("\nFCFS and SJF tests:")

    results = []
    results.append(fcfs(processes, latency))
    results.append(sjf(processes, latency))

    for r in results:
        print_algorithm_result(r)


if __name__ == "__main__":
    main()