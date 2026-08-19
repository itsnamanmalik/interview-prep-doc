---
icon: fontawesome/brands/python
---

# Advanced Python

### 1. **Decorators**

Decorators allow you to modify the behavior of a function or class method.

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function execution")
        result = func(*args, **kwargs)
        print("After function execution")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}")

say_hello("Naman")
```

**Output**:

```
Before function execution
Hello, Naman
After function execution
```

### 2. **Context Managers**

Context managers ensure that resources are properly managed, typically used with the `with` statement.

```python
class MyContextManager:
    def __enter__(self):
        print("Entering context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context")

with MyContextManager():
    print("Inside the context")
```

**Output**:

```
Entering context
Inside the context
Exiting context
```

### 3. **Metaclasses**

Metaclasses allow you to modify the class creation process.

```python
class Meta(type):
    def __new__(cls, name, bases, dct):
        print(f"Creating class {name}")
        return super().__new__(cls, name, bases, dct)

class MyClass(metaclass=Meta):
    pass

obj = MyClass()
```

**Output**:

```
Creating class MyClass
```

### 4. **Coroutines and** `**asyncio**`

Python's `asyncio` library allows you to write asynchronous code.

```python
import asyncio

async def greet():
    print("Hello!")
    await asyncio.sleep(1)
    print("How are you?")

async def main():
    await asyncio.gather(greet(), greet())

asyncio.run(main())
```

**Output**:

```
Hello!
Hello!
(after 1 second)
How are you?
How are you?
```

### 5. **Generators and** `**yield**`

Generators are functions that return an iterator and allow you to iterate over a sequence of values lazily.

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

for i in countdown(5):
    print(i)
```

**Output**:

```
5
4
3
2
1
```

### 6. **Descriptor Protocol**

Descriptors are Python objects that implement one of the `__get__`, `__set__`, or `__delete__` methods.

```python
class Descriptor:
    def __get__(self, instance, owner):
        print("Getting value")
        return instance._value

    def __set__(self, instance, value):
        print("Setting value")
        instance._value = value

class MyClass:
    attr = Descriptor()

    def __init__(self, value):
        self.attr = value

obj = MyClass(10)
print(obj.attr)
```

**Output**:

```
Setting value
Getting value
10
```

### 7. **Memory Management and** `**__slots__**`

`__slots__` allow you to limit the attributes that an object can have, reducing memory overhead.

```python
class MyClass:
    __slots__ = ['name', 'age']

    def __init__(self, name, age):
        self.name = name
        self.age = age

obj = MyClass('Naman', 30)
print(obj.name, obj.age)
```

### 8. **Multithreading and Multiprocessing**

Python provides threading and multiprocessing libraries for concurrent and parallel execution.

```python
import threading

def print_numbers():
    for i in range(5):
        print(i)

thread = threading.Thread(target=print_numbers)
thread.start()
thread.join()
```

**Output**:

```
0
1
2
3
4
```

Similarly, you can use `multiprocessing` for parallelism by running tasks in separate processes.

### 9. **Custom Iterators**

Python allows you to create custom iterators by implementing `__iter__()` and `__next__()` methods.

```python
class MyIterator:
    def __init__(self, start, end):
        self.current = start
        self.end = end

    def __iter__(self):
        return self

    def __next__(self):
        if self.current > self.end:
            raise StopIteration
        else:
            self.current += 1
            return self.current - 1

for i in MyIterator(1, 5):
    print(i)
```

**Output**:

```
1
2
3
4
5
```

### 10. **Abstract Base Classes (ABC)**

Abstract base classes (ABCs) define a set of methods that must be created within any child classes.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius ** 2

circle = Circle(5)
print(circle.area())
```

**Output**:

```
78.5
```

These are just a few advanced Python topics that touch on decorators, metaprogramming, concurrency, memory management, and abstract classes. Let me know if you'd like more examples or deeper explanations!
