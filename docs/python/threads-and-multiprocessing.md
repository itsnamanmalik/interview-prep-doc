---
icon: material/cpu-64-bit
---

# Threads & Multiprocessing

In Python, both threads and multiprocessing can be used to achieve concurrency, but they serve different purposes and have different trade-offs.

- **Threads**: Allow multiple threads to execute concurrently in the same process, sharing the same memory space. Useful for I/O-bound tasks but limited by the Global Interpreter Lock (GIL), which prevents multiple native threads from executing Python bytecodes at once.

- **Multiprocessing**: Involves creating separate processes, each with its own memory space. It bypasses the GIL, making it suitable for CPU-bound tasks.

### 1. Threads in Python

### **Example: Using Threads to Perform Concurrent I/O Tasks**

```python
import threading
import time

# Function to simulate an I/O-bound task
def io_task(name, delay):
    print(f"Thread {name}: Starting")
    time.sleep(delay)
    print(f"Thread {name}: Finished after {delay} seconds")

# Main function to create and start threads
def main():
    threads = []
    
    # Create threads
    for i in range(5):
        t = threading.Thread(target=io_task, args=(f'Thread-{i+1}', i+1))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print("All threads completed")

if __name__ == "__main__":
    main()
```

### **Explanation:**

- `**threading.Thread()**`: Creates a new thread. The `target` argument specifies the function to run, and `args` passes arguments to that function.

- `**t.start()**`: Starts the thread.

- `**t.join()**`: Waits for the thread to complete before proceeding.

### 2. Multiprocessing in Python

### **Example: Using Multiprocessing for CPU-Bound Tasks**

```python
import multiprocessing
import time

# Function to simulate a CPU-bound task
def cpu_task(name, n):
    print(f"Process {name}: Starting")
    result = sum([i * i for i in range(n)])
    print(f"Process {name}: Finished with result {result}")

# Main function to create and start processes
def main():
    processes = []
    
    # Create processes
    for i in range(5):
        p = multiprocessing.Process(target=cpu_task, args=(f'Process-{i+1}', 10**6))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    print("All processes completed")

if __name__ == "__main__":
    main()
```

### **Explanation:**

- `**multiprocessing.Process()**`: Creates a new process. The `target` argument specifies the function to run, and `args` passes arguments to that function.

- `**p.start()**`: Starts the process.

- `**p.join()**`: Waits for the process to complete before proceeding.

### Comparison of Threads vs. Multiprocessing

## Treads Vs Multiprocessing

| Feature | Threads | Multiprocessing |
| --- | --- | --- |
| **Concurrency** | Limited by the GIL, better for I/O-bound | Not limited by the GIL, better for CPU-bound |
| **Memory** | Shared memory space between threads | Separate memory space for each process |
| **Overhead** | Low overhead, lightweight | Higher overhead due to process creation |
| **Use Case** | I/O-bound tasks (e.g., file I/O, network) | CPU-bound tasks (e.g., computations) |

### Practical Considerations:

- **Threads** are great for tasks like reading/writing files, network operations, or any task that involves waiting on I/O.

- **Multiprocessing** is ideal for tasks that need to utilize multiple CPU cores, such as heavy computations.

### Example: Using ThreadPoolExecutor and ProcessPoolExecutor

Python's `concurrent.futures` module provides high-level abstractions for threading and multiprocessing.

### **ThreadPoolExecutor Example:**

```python
from concurrent.futures import ThreadPoolExecutor
import time

def io_task(name, delay):
    print(f"Task {name}: Starting")
    time.sleep(delay)
    print(f"Task {name}: Finished after {delay} seconds")

def main():
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(io_task, f'Task-{i+1}', i+1) for i in range(5)]
        
        for future in futures:
            future.result()  # Wait for each task to complete

if __name__ == "__main__":
    main()
```

### **ProcessPoolExecutor Example:**

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_task(n):
    return sum([i * i for i in range(n)])

def main():
    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(cpu_task, 10**6) for _ in range(5)]
        
        for future in futures:
            print(f"Result: {future.result()}")

if __name__ == "__main__":
    main()
```

These examples show how to use thread and process pools, which automatically manage a pool of workers, making it easier to execute tasks concurrently.
