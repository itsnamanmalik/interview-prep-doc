---
icon: material/sync
---

# Iterators

Iterators are objects in Python that represent a stream of data. An iterator is any object that implements two specific methods: `__iter__()` and `__next__()`. Iterators provide a way to access elements of a collection (like a list or a dictionary) one at a time, without needing to store all elements in memory simultaneously. This makes iterators useful for working with large data sets or infinite sequences.

### Key Features of Iterators

1. **State Retention**: Iterators maintain their internal state and produce the next item in the sequence when you call the `__next__()` method. This state retention is what allows the iterator to continue from where it left off each time `__next__()` is called.

1. **Exhaustion**: Once an iterator has iterated over all of its elements, it is considered "exhausted." Any further calls to `__next__()` will raise a `StopIteration` exception, signaling that there are no more items to retrieve.

1. **Iterability**: An iterator is iterable, meaning it can be used in a loop or passed to functions like `next()` that work with iterable objects.

### How to Create an Iterator

To create an iterator, you need to define a class with the following:

- An `__iter__()` method that returns the iterator object itself.

- A `__next__()` method that returns the next item in the sequence. If there are no more items, `__next__()` should raise a `StopIteration` exception.

Here's a simple example of a custom iterator:

```python
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        else:
            self.current -= 1
            return self.current + 1

# Using the iterator
countdown = Countdown(5)
for number in countdown:
    print(number)
```

Output:

```
5
4
3
2
1
```

### Built-in Iterators in Python

Python provides many built-in iterators for different data types:

- **Lists, Tuples, and Strings**: All these types are iterable. When you use a `for` loop to iterate over them, Python internally uses an iterator to retrieve each element one by one.

```python
my_list = [1, 2, 3, 4]
my_iter = iter(my_list)  # Get an iterator from the list
print(next(my_iter))  # Output: 1
print(next(my_iter))  # Output: 2
```

- **Dictionaries**: Iterating over a dictionary will yield its keys by default. To get the values or items, you can use `.values()` or `.items()`.

```python
my_dict = {'a': 1, 'b': 2}
for key in my_dict:
    print(key)  # Outputs: 'a', then 'b'
```

- **Files**: File objects in Python are iterators that yield lines of the file one at a time.

```python
with open('example.txt', 'r') as file:
    for line in file:
        print(line, end='')
```

### Using the `iter()` and `next()` Functions

- `**iter()**`: This function returns an iterator object. It can be used to get an iterator from an iterable, such as a list, tuple, or string.

- `**next()**`: This function retrieves the next item from an iterator. If the iterator is exhausted, `next()` raises a `StopIteration` exception.

```python
my_tuple = (1, 2, 3)
tuple_iter = iter(my_tuple)

print(next(tuple_iter))  # Output: 1
print(next(tuple_iter))  # Output: 2
print(next(tuple_iter))  # Output: 3
# print(next(tuple_iter))  # Raises StopIteration
```

### Differences Between Iterators and Generators

- **Syntax**: Generators are defined using functions with the `yield` keyword, whereas iterators are defined using classes with `__iter__()` and `__next__()` methods.

- **Ease of Use**: Generators are typically easier to write and understand than iterators because they don't require the boilerplate code for state management.

- **Memory Usage**: Both generators and iterators are memory efficient, but generators provide a more Pythonic way to handle sequences of data without managing state manually.

### When to Use Iterators

- **Custom Iteration Logic**: Use iterators when you need a custom object that behaves like an iterable with complex logic that doesn't fit the simple generator function pattern.

- **Reusability and Flexibility**: Iterators offer more control over the iteration process, allowing for multiple iterators over the same dataset or customizing the iteration process.

Iterators are a core concept in Python for managing sequential data and allow for lazy evaluation, efficient looping, and simplified code management when working with large or infinite data sets.
