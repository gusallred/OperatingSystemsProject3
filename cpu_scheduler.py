"""
/************************************************
 CS 440 Operating Systems
 Project 3 CPU Scheduling Simulation
 Names: Augustus Allred, David Gonzalez
 Date: 3/13/2026
************************************************/
"""

from dataclasses import dataclass, field
from collections import deque
import copy
import random


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    remaining: int = field(init=False)
    first_start: int = None
    completion: int = None

    def __post_init__(self):
        self.remaining = self.burst


def clone_processes(processes):
    return copy.deepcopy(processes)


def read_int(prompt, minimum, maximum):
    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Please enter an integer from {minimum} to {maximum}.")
        except ValueError:
            print("Invalid input. Please enter an integer.")


def generate_processes(seed, num_processes, last_arrival, max_burst):
    rng = random.Random(seed)
    processes = []

    for i in range(1, num_processes + 1):
        arrival = rng.randint(0, last_arrival)
        burst = rng.randint(1, max_burst)
        processes.append(Process(f"P{i}", arrival, burst))

    return processes


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
    switch_count = 0
    previous_pid = None

    while not all_complete(procs):
        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.arrival, int(p.pid[1:]))
        )

        if not ready:
            time = get_next_arrival_time(procs, time)
            previous_pid = None
            continue

        if previous_pid is not None:
            switch_count += 1
            if latency > 0:
                trace.append(f"@t={time}, context switch {switch_count} occurs")
                time += latency
                ready = sorted(
                    get_ready_processes(procs, time),
                    key=lambda p: (p.arrival, int(p.pid[1:]))
                )

        current = ready[0]
        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)

        if not all_complete(procs) and get_ready_processes(procs, time):
            previous_pid = current.pid
        else:
            previous_pid = None

    trace.append(f"@t={time}, all processes complete")
    return make_result("FCFS", procs, trace)


def sjf(processes, latency):
    procs = clone_processes(processes)
    trace = []
    time = 0
    switch_count = 0
    previous_pid = None

    while not all_complete(procs):
        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.burst, p.arrival, int(p.pid[1:]))
        )

        if not ready:
            time = get_next_arrival_time(procs, time)
            previous_pid = None
            continue

        if previous_pid is not None:
            switch_count += 1
            if latency > 0:
                trace.append(f"@t={time}, context switch {switch_count} occurs")
                time += latency
                ready = sorted(
                    get_ready_processes(procs, time),
                    key=lambda p: (p.burst, p.arrival, int(p.pid[1:]))
                )

        current = ready[0]
        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)

        if not all_complete(procs) and get_ready_processes(procs, time):
            previous_pid = current.pid
        else:
            previous_pid = None

    trace.append(f"@t={time}, all processes complete")
    return make_result("SJF", procs, trace)


def srtf(processes, latency):
    procs = clone_processes(processes)
    trace = []
    time = 0
    current = None
    previous_pid = None
    switch_count = 0

    while not all_complete(procs):
        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.remaining, p.arrival, int(p.pid[1:]))
        )

        if current is None:
            if not ready:
                time = get_next_arrival_time(procs, time)
                previous_pid = None
                continue

            chosen = ready[0]

            if previous_pid is not None and chosen.pid != previous_pid:
                switch_count += 1
                if latency > 0:
                    trace.append(f"@t={time}, context switch {switch_count} occurs")
                    time += latency
                    previous_pid = None
                    continue

            current = chosen

        next_arrival = get_next_arrival_time(procs, time)

        if next_arrival is None:
            run_time = current.remaining
        else:
            run_time = min(current.remaining, next_arrival - time)

        trace.append(f"@t={time}, {current.pid} selected for {run_time} units")
        time = run_for(current, run_time, time)

        if current.remaining == 0:
            if not all_complete(procs) and get_ready_processes(procs, time):
                previous_pid = current.pid
            else:
                previous_pid = None
            current = None
            continue

        ready = sorted(
            get_ready_processes(procs, time),
            key=lambda p: (p.remaining, p.arrival, int(p.pid[1:]))
        )

        best = ready[0]

        if best.pid != current.pid and best.remaining < current.remaining:
            previous_pid = current.pid
            current = None
    
    trace.append(f"@t={time}, all processes complete")
    return make_result("SRTF", procs, trace)


def rr(processes, quantum, latency):
    procs = clone_processes(processes)
    trace = []
    time = 0
    current = None
    previous_pid = None
    switch_count = 0

    arrivals = sorted(procs, key=lambda p: (p.arrival, int(p.pid[1:])))
    arrival_index = 0
    ready_queue = deque()

    def add_arrivals(now):
        nonlocal arrival_index
        while arrival_index < len(arrivals) and arrivals[arrival_index].arrival <= now:
            p = arrivals[arrival_index]
            if p.remaining > 0 and p is not current and p not in ready_queue:
                ready_queue.append(p)
            arrival_index += 1

    while not all_complete(procs):
        add_arrivals(time)

        if current is None:
            if not ready_queue:
                time = get_next_arrival_time(procs, time)
                previous_pid = None
                add_arrivals(time)

            if previous_pid is not None and ready_queue:
                switch_count += 1
                if latency > 0:
                    trace.append(f"@t={time}, context switch {switch_count} occurs")
                    time += latency
                    add_arrivals(time)

            if not ready_queue:
                continue

            current = ready_queue.popleft()

        run_time = min(quantum, current.remaining)
        trace.append(f"@t={time}, {current.pid} selected for {run_time} units")
        time = run_for(current, run_time, time)
        add_arrivals(time)

        if current.remaining == 0:
            if ready_queue:
                previous_pid = current.pid
            else:
                previous_pid = None
            current = None
        else:
            if ready_queue:
                ready_queue.append(current)
                previous_pid = current.pid
                current = None
            # if queue is empty, same process keeps running next time with no switch

    trace.append(f"@t={time}, all processes complete")
    return make_result(f"RR (q={quantum})", procs, trace)


def random_selection(processes, latency, rng):
    procs = clone_processes(processes)
    trace = []
    time = 0
    switch_count = 0
    previous_pid = None

    while not all_complete(procs):
        ready = get_ready_processes(procs, time)

        if not ready:
            time = get_next_arrival_time(procs, time)
            previous_pid = None
            continue

        if previous_pid is not None:
            switch_count += 1
            if latency > 0:
                trace.append(f"@t={time}, context switch {switch_count} occurs")
                time += latency
                ready = get_ready_processes(procs, time)

        current = rng.choice(ready)
        trace.append(f"@t={time}, {current.pid} selected for {current.remaining} units")
        time = run_for(current, current.remaining, time)

        if not all_complete(procs) and get_ready_processes(procs, time):
            previous_pid = current.pid
        else:
            previous_pid = None

    trace.append(f"@t={time}, all processes complete")
    return make_result("Random", procs, trace)


def main():
    seed = read_int("Enter random seed: ", 0, 10**9)
    num_processes = read_int("Enter number of processes (2-10): ", 2, 10)
    last_arrival = read_int("Enter last arrival time (0-99): ", 0, 99)
    max_burst = read_int("Enter maximum burst time (1-100): ", 1, 100)
    quantum = read_int("Enter RR quantum (1-100): ", 1, 100)
    latency = read_int("Enter context-switch latency (0-10): ", 0, 10)

    processes = generate_processes(seed, num_processes, last_arrival, max_burst)

    print()
    print_process_table(processes)
    print(f"Context-switch latency L = {latency}")
    print(f"RR quantum q = {quantum}")

    results = [
        fcfs(processes, latency),
        sjf(processes, latency),
        srtf(processes, latency),
        rr(processes, quantum, latency),
        random_selection(processes, latency, random.Random(seed))
    ]

    for result in results:
        print_algorithm_result(result)

    print_checksum(results)


if __name__ == "__main__":
    main()