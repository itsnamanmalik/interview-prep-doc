---
icon: material/file-document-outline
---

# Generators

Generators in Python are a special type of iterable, like lists or tuples, but they do not store their contents in memory. Instead, they generate values on the fly and yield them one at a time. This makes them memory efficient and particularly useful for handling large datasets or streams of data.

### Key Features of Generators

1. **Lazy Evaluation**: Generators compute values one at a time as they are needed, rather than computing and storing them all at once. This reduces memory usage and can make programs more efficient.

1. **Use of** `**yield**` **Keyword**: Generators use the `yield` statement to produce a series of values. When a generator function calls `yield`, it pauses the function's state, saves it, and returns the yielded value to the caller. The function can be resumed later, continuing from where it left off.

1. **Simpler Code**: They allow for the creation of iterators with less boilerplate code. Writing a generator function is often easier and cleaner than writing an equivalent iterator class.

### How to Create a Generator

A generator can be created in two ways:

### **1. Generator Functions**

A generator function is defined like a regular function but uses the `yield` statement instead of `return` to provide a value to the caller.

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

# Using the generator
for number in countdown(5):
    print(number)
```

In this example, the `countdown` function is a generator that yields numbers from `n` down to `1`. Each call to `yield` pauses the function and returns the current value of `n`.

### **2. Generator Expressions**

Generator expressions provide a more compact way to create generators, similar to list comprehensions but with parentheses instead of square brackets.

```python
# Generator expression
squares = (x * x for x in range(5))

# Using the generator
for square in squares:
    print(square)
```

This creates a generator that yields the squares of numbers from `0` to `4`.

### Benefits of Using Generators

- **Memory Efficiency**: Generators are more memory efficient than lists, especially for large data sets, because they yield one item at a time and do not store all items in memory.

- **Improved Performance**: Since generators yield values one at a time and only when required, they can be faster than equivalent operations that need to load all data into memory first.

- **Cleaner Code**: Generators often lead to cleaner and more readable code, especially for complex iteration logic.

### When to Use Generators

Use generators when:

- You are working with large datasets that do not fit into memory.

- You need to create an iterable object but do not need to store all elements at once.

- You want to create a pipeline of operations that can be processed element by element.

Generators are a powerful feature in Python that can help make your code more efficient and easier to read, especially when dealing with large or complex data streams.
