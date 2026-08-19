---
icon: material/ungroup
---

# Object Oriented Programming

Here's a concise overview of Object-Oriented Programming (OOP) concepts in Python, including types of methods and other key concepts:

### 1. **Class and Object**

- **Class**: A blueprint for creating objects (a template).

- **Object**: An instance of a class.

**Example:**

```python
class Dog:
    def __init__(self, name, breed):
        self.name = name
        self.breed = breed

dog1 = Dog("Buddy", "Golden Retriever")
```

### 2. **Attributes and Methods**

- **Attributes**: Variables that belong to a class or an object.

- **Methods**: Functions defined inside a class that describe the behaviors of an object.

**Example:**

```python
class Dog:
    species = "Canine"  # Class attribute

    def __init__(self, name, breed):  # Constructor method
        self.name = name              # Instance attribute
        self.breed = breed            # Instance attribute

    def bark(self):                   # Instance method
        return f"{self.name} says woof!"

dog1 = Dog("Buddy", "Golden Retriever")
print(dog1.bark())  # Output: Buddy says woof!
```

### 3. **Types of Methods**

- **Instance Methods**: Operate on instances of the class. The first parameter is always `self`, which refers to the instance.

- **Class Methods**: Operate on the class itself. The first parameter is `cls`, which refers to the class. Defined using the `@classmethod` decorator.

- **Static Methods**: Do not operate on an instance or the class; they are independent. Defined using the `@staticmethod` decorator.

**Example:**

```python
class Example:
    def instance_method(self):
        print("This is an instance method.")

    @classmethod
    def class_method(cls):
        print("This is a class method.")

    @staticmethod
    def static_method():
        print("This is a static method.")

obj = Example()
obj.instance_method()  # Output: This is an instance method.
Example.class_method() # Output: This is a class method.
Example.static_method() # Output: This is a static method.
```

### 4. **Inheritance**

- Allows a class (child class) to inherit attributes and methods from another class (parent class).

- Supports code reuse and the creation of a hierarchical class structure.

**Example**

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "Sound"

class Dog(Animal):  # Inherits from Animal
    def speak(self):
        return "Woof!"

dog = Dog("Buddy")
print(dog.speak())  # Output: Woof!
```

### 5. **Encapsulation**

- Restricts access to certain methods and variables, encapsulating the data for security.

- Use underscore (`_`) or double underscore (`__`) to indicate private attributes or methods.

**Example:**

```python
class Car:
    def __init__(self, brand):
        self.__brand = brand  # Private attribute

    def get_brand(self):
        return self.__brand

car = Car("Toyota")
print(car.get_brand())  # Output: Toyota
```

### 6. **Polymorphism**

- Allows methods to have the same name but behave differently depending on the object calling them.

- Achieved through method overriding and duck typing.

**Example:**

```python
class Bird:
    def speak(self):
        return "Chirp!"

class Duck(Bird):
    def speak(self):
        return "Quack!"

def make_sound(bird):
    print(bird.speak())

bird = Bird()
duck = Duck()
make_sound(bird)  # Output: Chirp!
make_sound(duck)  # Output: Quack!
```

### 7. **Abstraction**

- Hides the complex implementation details and shows only the essential features of an object.

- Can be achieved using abstract classes and methods.

**Example:**

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def move(self):
        pass

class Fish(Animal):
    def move(self):
        return "Swims"

fish = Fish()
print(fish.move())  # Output: Swims
```

These bullet points cover the core concepts of OOP in Python, illustrating how classes and objects work, the different types of methods, and fundamental principles like inheritance, encapsulation, polymorphism, and abstraction.
