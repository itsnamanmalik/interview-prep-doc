---
icon: material/code-tags
---

# Decorators

Decorators in Python are a powerful feature that allows you to modify or enhance the behavior of functions or methods without changing their actual code. Decorators are commonly used for logging, access control, memoization, and more.

Here's a basic overview and example to illustrate how decorators work:

### Basic Concept

A decorator is a function that takes another function as an argument and extends or alters its behavior. It is applied to a function using the `@decorator_name` syntax.

### Example: A Simple Decorator

Let's create a simple decorator that prints the arguments and result of a function:

```python
# Define the decorator
def debug_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Arguments: {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"Result: {result}")
        return result
    return wrapper

# Apply the decorator to a function
@debug_decorator
def add(a, b):
    return a + b

# Call the decorated function
add(3, 4)
```

### How It Works

1. **Define the Decorator**:

    - `debug_decorator` is a function that takes another function (`func`) as its argument.

    - Inside `debug_decorator`, we define a `wrapper` function that adds extra behavior before and after calling the original function.

    - `wrapper` prints the arguments and result, then calls the original function (`func`).

1. **Apply the Decorator**:

    - Using `@debug_decorator` before the `add` function definition applies the decorator to `add`.

    - When `add(3, 4)` is called, it triggers the `wrapper` function from the decorator, which prints the arguments and result before and after calling `add`.

### Output

```
Arguments: (3, 4), {}
Result: 7
```

### Example: Using Decorators with Arguments

Decorators can also accept arguments. Here’s an example of a decorator that measures the execution time of a function:

```python
import time

def timing_decorator(unit="seconds"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            if unit == "milliseconds":
                elapsed_time *= 1000
            print(f"Execution time: {elapsed_time:.4f} {unit}")
            return result
        return wrapper
    return decorator

@timing_decorator(unit="milliseconds")
def slow_function(n):
    time.sleep(n)
    return "Done"

slow_function(2)
```

In this example:

- `timing_decorator` takes an argument `unit` to specify the time unit.

- The `decorator` function wraps the original function and measures its execution time.

- The `wrapper` function calculates and prints the elapsed time based on the specified unit.
