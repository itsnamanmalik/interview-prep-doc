---
icon: material/format-list-checks
---

# Async.IO

`asyncio` is a library in Python used for writing concurrent code using the `async`/`await` syntax. It is particularly useful for I/O-bound tasks, such as handling multiple network connections, where traditional threading or multiprocessing might be overkill or inefficient.

Here's a simple example to demonstrate how `asyncio` works in Python:

### Example: Fetching Data from Multiple URLs Concurrently

```python
import asyncio
import aiohttp

# An async function to fetch data from a URL
async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.text()

# An async function to fetch data from multiple URLs concurrently
async def fetch_all_data(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(fetch_data(session, url))
        return await asyncio.gather(*tasks)

# Main function to run the asyncio event loop
def main():
    urls = [
        'https://example.com',
        'https://httpbin.org/get',
        'https://jsonplaceholder.typicode.com/posts/1'
    ]
    
    # Running the event loop
    results = asyncio.run(fetch_all_data(urls))
    
    # Printing the results
    for i, result in enumerate(results):
        print(f"Data from URL {i+1}: {result[:100]}...")  # Printing the first 100 characters of the response

if __name__ == "__main__":
    main()
```

### Explanation:

1. `**async def fetch_data(session, url):**`: This is an asynchronous function that fetches data from a given URL using an `aiohttp.ClientSession`.

1. `**async def fetch_all_data(urls):**`: This function creates a session and then concurrently fetches data from all the provided URLs. The `asyncio.gather(*tasks)` method is used to run all the tasks concurrently.

1. `**asyncio.run(fetch_all_data(urls)):**`: This function is used to run the `fetch_all_data` coroutine. `asyncio.run` creates a new event loop, runs the coroutine until it completes, and then closes the loop.

1. `**aiohttp.ClientSession**`: This is used for making HTTP requests in an asynchronous manner. The `with` statement ensures the session is properly closed after use.

### Benefits of Using `asyncio`:

- **Efficiency**: `asyncio` allows you to handle thousands of I/O-bound tasks efficiently using a single thread.

- **Non-blocking**: The `await` keyword allows the function to yield control back to the event loop, so other tasks can run while waiting for an I/O operation to complete.

### Example: Simple Asynchronous Task Scheduling

Here's another example that demonstrates basic asynchronous task scheduling:

```python
import asyncio

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    print("Starting...")
    
    # Schedule the tasks to run concurrently
    task1 = asyncio.create_task(say_after(2, 'Hello'))
    task2 = asyncio.create_task(say_after(3, 'World'))
    
    # Wait for both tasks to finish
    await task1
    await task2
    
    print("Finished")

# Run the event loop
asyncio.run(main())
```

### Output:

```
Starting...
Hello
World
Finished
```

### Explanation:

- `**asyncio.create_task()**`: This function schedules the coroutine to run in the background and returns a `Task` object.

- `**await task1**` **and** `**await task2**`: These ensure that the program waits for the tasks to complete before proceeding.

With these examples, you can see how `asyncio` enables efficient asynchronous programming in Python.
