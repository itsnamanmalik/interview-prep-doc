---
icon: material/view-grid-outline
---

# Design Patterns

Design patterns are solutions to common problems in software design. They are categorized into three main types: creational, structural, and behavioral. Here’s a brief overview of each category with Python implementations:

## 1. Creational Patterns

**Creational patterns** deal with object creation mechanisms, trying to create objects in a manner suitable to the situation.

### **a. Singleton Pattern**

Ensures that a class has only one instance and provides a global point of access to that instance.

```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

# Usage
s1 = Singleton()
s2 = Singleton()
print(s1 is s2)  # True
```

### **b. Factory Method Pattern**

Provides an interface for creating objects, but allows subclasses to alter the type of objects that will be created.

```python
class Product:
    def operation(self):
        pass

class ConcreteProductA(Product):
    def operation(self):
        return "ConcreteProductA"

class ConcreteProductB(Product):
    def operation(self):
        return "ConcreteProductB"

class Creator:
    def factory_method(self):
        pass

    def operation(self):
        product = self.factory_method()
        return f"Creator: The same creator's code just worked with {product.operation()}"

class ConcreteCreatorA(Creator):
    def factory_method(self):
        return ConcreteProductA()

class ConcreteCreatorB(Creator):
    def factory_method(self):
        return ConcreteProductB()

# Usage
creator = ConcreteCreatorA()
print(creator.operation())  # Creator: The same creator's code just worked with ConcreteProductA
```

## 2. Structural Patterns

**Structural patterns** focus on how classes and objects are composed to form larger structures.

### **a. Adapter Pattern**

Allows incompatible interfaces to work together.

```python
class Target:
    def request(self):
        return "Target: The default behavior."

class Adaptee:
    def specific_request(self):
        return "Adaptee: Specific behavior."

class Adapter(Target):
    def __init__(self, adaptee):
        self._adaptee = adaptee

    def request(self):
        return self._adaptee.specific_request()

# Usage
adaptee = Adaptee()
adapter = Adapter(adaptee)
print(adapter.request())  # Adaptee: Specific behavior.
```

### **b. Decorator Pattern**

Allows behavior to be added to individual objects, either statically or dynamically, without affecting the behavior of other objects from the same class.

```python
class Component:
    def operation(self):
        return "Component"

class Decorator:
    def __init__(self, component):
        self._component = component

    def operation(self):
        return self._component.operation()

class ConcreteDecoratorA(Decorator):
    def operation(self):
        return f"ConcreteDecoratorA({self._component.operation()})"

# Usage
component = Component()
decorated = ConcreteDecoratorA(component)
print(decorated.operation())  # ConcreteDecoratorA(Component)
```

## 3. Behavioral Patterns

**Behavioral patterns** are concerned with algorithms and the assignment of responsibilities between objects.

### **a. Observer Pattern**

Defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically.

```python
class Observer:
    def update(self, message):
        pass

class ConcreteObserver(Observer):
    def update(self, message):
        print(f"Observer received message: {message}")

class Subject:
    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self, message):
        for observer in self._observers:
            observer.update(message)

# Usage
subject = Subject()
observer = ConcreteObserver()
subject.add_observer(observer)
subject.notify_observers("Hello Observers!")  # Observer received message: Hello Observers!
```

### **b. Strategy Pattern**

Defines a family of algorithms, encapsulates each one, and makes them interchangeable.

```python
class Strategy:
    def execute(self, data):
        pass

class ConcreteStrategyA(Strategy):
    def execute(self, data):
        return f"Strategy A with {data}"

class ConcreteStrategyB(Strategy):
    def execute(self, data):
        return f"Strategy B with {data}"

class Context:
    def __init__(self, strategy):
        self._strategy = strategy

    def set_strategy(self, strategy):
        self._strategy = strategy

    def execute_strategy(self, data):
        return self._strategy.execute(data)

# Usage
context = Context(ConcreteStrategyA())
print(context.execute_strategy("data"))  # Strategy A with data
context.set_strategy(ConcreteStrategyB())
print(context.execute_strategy("data"))  # Strategy B with data
```
