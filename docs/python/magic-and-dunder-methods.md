---
icon: material/auto-fix
---

# Magic & Dunder Methods

***Python Magic methods*** *are the methods starting and ending with double underscores ‘__’. They are defined by built-in classes in Python and commonly used for operator overloading.*

They are also called **Dunder methods,** Dunder here means “Double Under (Underscores)”.

## Python Magic Methods

Built in classes define many magic methods, **dir()** function can show you magic methods inherited by a class.

**Example:**

This code displays the magic methods inherited by **int** class.

```python
# code
print(dir(int))
```

**Output**

```
['__abs__', '__add__', '__and__', '__bool__', '__ceil__', '__class__', '__delattr__', '__dir__', '__divmod__', '__doc__', '__eq__', '__float__', '__floor__', '__floordiv__', '__format__', '__ge__', '_...
```

Or, you can try cmd/terminal to get the list of magic functions in Python, open cmd or terminal, type python3 to go to the Python console, and type:

```
>>> dir(int)
```

**Output:**

```
__bool__            __init__               __reduce__          __sub__
__ceil__            __init_subclass__      __reduce_ex__       __subclasshook__
__class__           __int__                __repr__            __truediv__
__delattr__         __invert__             __rfloordiv__       __trunc__
__dir__             __le__                 __rlshift__         __xor__
__divmod__          __lshift__             __rmod__            as_integer_ratio
__doc__             __lt__                 __rmul__            bit_count
__eq__              __mod__                __ror__             bit_length
__float__           __mul__                __round__           conjugate
__floor__           __ne__                 __rpow__            denominator
__floordiv__        __neg__                __rrshift__         from_bytes
__format__          __new__                __rshift__          imag
__ge__              __or__                 __rsub__            numerator
__getattribute__    __pos__                __rtruediv__        real
```

## Python Magic Methods

Below are the lists of Python magic methods and their uses.

> **Initialization and Construction**

- **[__new__](https://www.geeksforgeeks.org/__new__-in-python/)****:** To get called in an object’s instantiation.

- **[__init__](https://www.geeksforgeeks.org/__init__-in-python/)****:** To get called by the __new__ method.

- **[__del__](https://www.geeksforgeeks.org/python-__delete__-vs-__del__/)****:** It is the destructor.

> **Numeric magic methods**

- **[__trunc__](https://www.geeksforgeeks.org/g-fact-35-truncate-in-python/)****(self):** Implements behavior for math.trunc()

- **[__ceil__](https://www.geeksforgeeks.org/__call__-in-python/)****(self):** Implements behavior for math.ceil()

- **[__floor__](https://www.geeksforgeeks.org/python-math-floor-function/)****(self):** Implements behavior for math.floor()

- **[__round__](https://www.geeksforgeeks.org/round-function-python/)****(self,n):** Implements behavior for the built-in round()

- **__invert__(self):** Implements behavior for inversion using the ~ operator.

- **__abs__(self):** Implements behavior for the built-in abs()

- **__neg__(self):** Implements behavior for negation

- **__pos__(self):** Implements behavior for unary positive

> **Arithmetic operators**

- __add__(self, other): Implements behavior for the + operator (addition).

- __sub__(self, other): Implements behavior for the – operator (subtraction).

- __mul__(self, other): Implements behavior for the * operator (multiplication).

- __floordiv__(self, other): Implements behavior for the // operator (floor division).

- __truediv__(self, other): Implements behavior for the / operator (true division).

- __mod__(self, other): Implements behavior for the % operator (modulus).

- __divmod__(self, other): Implements behavior for the divmod() function.

- __pow__(self, other): Implements behavior for the ** operator (exponentiation).

- __lshift__(self, other): Implements behavior for the << operator (left bitwise shift).

- __rshift__(self, other): Implements behavior for the >> operator (right bitwise shift).

- __and__(self, other): Implements behavior for the & operator (bitwise and).

- __or__(self, other): Implements behavior for the | operator (bitwise or).

- __xor__(self, other): Implements behavior for the ^ operator (bitwise xor).

- __invert__(self): Implements behavior for bitwise NOT using the ~ operator.

- __neg__(self): Implements behavior for negation using the – operator.

- __pos__(self): Implements behavior for unary positive using the + operator.

> **String Magic Methods**

- **[__str__](https://www.geeksforgeeks.org/str-vs-repr-in-python/)****(self):** Defines behavior for when str() is called on an instance of your class.

- **[__repr_](https://www.geeksforgeeks.org/python-__repr__-magic-method/)****_(self): T**o get called by built-int repr() method to return a machine readable representation of a type.

- **__unicode__(self):** This method to return an unicode string of a type.

- **__format__(self, formatstr):** return a new style of string.

- **[__hash_](https://www.geeksforgeeks.org/python-hash-method/)****_(self):** It has to return an integer, and its result is used for quick key comparison in dictionaries.

- **__nonzero__(self):** Defines behavior for when bool() is called on an instance of your class.

- **[__dir_](https://www.geeksforgeeks.org/python-dir-function/)****_(self):** This method to return a list of attributes of a class.

- **[__sizeof__(](https://www.geeksforgeeks.org/difference-between-__sizeof__-and-getsizeof-method-python/)****self):** It return the size of the object.

> **Comparison magic methods**

- **[__eq__](https://www.geeksforgeeks.org/difference-between-__eq__-vs-is-vs-in-python/)****(self, other):** Defines behavior for the equality operator, ==.

- **__ne__(self, other):** Defines behavior for the inequality operator, !=.

- **[__lt__](https://www.geeksforgeeks.org/python-__lt__-magic-method/)****(self, other):** Defines behavior for the less-than operator, <.

- **[__gt__](https://www.geeksforgeeks.org/customize-your-python-class-with-magic-or-dunder-methods/)****(self, other):** Defines behavior for the greater-than operator, >.

- **__le__(self, other):** Defines behavior for the less-than-or-equal-to operator, <=.

- **[__ge__](https://www.geeksforgeeks.org/customize-your-python-class-with-magic-or-dunder-methods/)****(self, other):** Defines behavior for the greater-than-or-equal-to operator, >=.

## Dunder or Magic Methods in Python

Let’s see some of the Python magic methods with examples:

### **1. __init__ method**

The **[__init__ method](https://www.geeksforgeeks.org/__init__-in-python/)** for initialization is invoked without any call, when an instance of a class is created, like constructors in certain other programming languages such as C++, Java, C#, PHP, etc.

These methods are the reason we can add two strings with the ‘+’ operator without any explicit typecasting.

```python
# declare our own string class
class String:
    # magic method to initiate object
    def __init__(self, string):
        self.string = string

# Driver Code
if __name__ == '__main__':
    # object creation
    string1 = String('Hello')
    # print object location
    print(string1)
```

**Output**

```
<__main__.String object at 0x7f538c059050>
```

### 2. __repr__ method

### **[__repr__ ](https://www.geeksforgeeks.org/python-__repr__-magic-method/)**method in Python defines how an object is presented as a string.

The below snippet of code prints only the memory address of the string object. Let’s add a __repr__ method to represent our object.

```python
# declare our own string class
class String:
    # magic method to initiate object
    def __init__(self, string):
        self.string = string

    # print our string object
    def __repr__(self):
        return 'Object: {}'.format(self.string)

# Driver Code
if __name__ == '__main__':
    # object creation
    string1 = String('Hello')
    # print object location
    print(string1)
```

**Output**

```
Object: Hello
```

**If we try to add a string to it:**

```python
# declare our own string class
class String:
    # magic method to initiate object
    def __init__(self, string):
        self.string = string

    # print our string object
    def __repr__(self):
        return 'Object: {}'.format(self.string)

# Driver Code
if __name__ == '__main__':
    # object creation
    string1 = String('Hello')
    # concatenate String object and a string
    print(string1 + ' world')
```

**Output:**

```
TypeError: unsupported operand type(s) for +: 'String' and 'str'
```

### 3. __add__ method

### **[__add__ method](https://www.geeksforgeeks.org/python-__add__-magic-method/)** in Python defines how the objects of a class will be added together. It is also known as overloaded addition operator.

Now add __add__ method to String class :

```python
# declare our own string class
class String:
    # magic method to initiate object
    def __init__(self, string):
        self.string = string

    # print our string object
    def __repr__(self):
        return 'Object: {}'.format(self.string)

    def __add__(self, other):
        return self.string + other

# Driver Code
if __name__ == '__main__':
    # object creation
    string1 = String('Hello')
    # concatenate String object and a string
    print(string1 + ' Geeks')
```

**Output**

```
Hello Geeks
```

We have discussed some of the Python magic methods or Dunder methods. Magic methods in Python can be used to different functionalities in your class.

Hope you learn about Python magic methods from this article, and use it in your projects.

## Dunder or magic methods in Python – FAQs

### What is a Dunder or Magic Method in Python?

> In Python, a “dunder” or “magic” method is a method that has double underscores before and after its name. These methods are not meant to be invoked directly by you, but the interpretation of them gets invoked internally by the Python interpreter to perform specific actions. For example, when you add two numbers with the `+` operator, the `__add__` method is invoked.

### What is the Python Magic Method?

> Magic methods in Python are special methods which have double underscores at the beginning and end of their names. They are also known as “special methods.” They are used to emulate the behavior of built-in types. For instance, `__init__`, `__add__`, `__len__`, `__repr__`, and many others are all magic methods. These methods enable us to use Python operators and built-in functions on our custom objects.

### What is `__le__` a Magic Method for?

> The `__le__` method in Python is a magic method used to define the behavior of the less than or equal to operator `<=`. It stands for “less than or equal to.” When you use the `<=` operator between two objects, Python internally calls the `__le__` method.

### **Example:**

```python
class Number:
    def __init__(self, value):
        self.value = value

    def __le__(self, other):
        return self.value <= other.value

# Usage
n1 = Number(5)
n2 = Number(10)
print(n1 <= n2)  # Output: True
```

### What is a Dunder?

> A “dunder” (short for double underscore) refers to the special methods in Python that are surrounded by double underscores (`__method__`). These methods are also known as magic methods. The term “dunder” is often used to highlight the special status these methods have in Python and their direct association with built-in Python behavior.

### What is the `__repr__` Magic Method in Python?

> The `__repr__` method in Python is a special magic method used to represent your object’s class instances as a string. The goal of `__repr__` is to be unambiguous and, if possible, match the string needed to recreate the object being represented. It’s often used for debugging and development. It’s good practice to define `__repr__` such that it returns a valid Python expression that could be used to recreate the object.

### **Example:**

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"Person(name='{self.name}', age={self.age})"

# Usage
p = Person("Alice", 30)
print(p)  # Output: Person(name='Alice', age=30)
```

> This implementation of `__repr__` provides a clear and concise description of the object that can be useful during debugging and logging.

Looking to dive into the world of programming or sharpen your Python skills? Our **[Master Python: Complete Beginner to Advanced Course](https://gfgcdn.com/tu/T3C/)** is your ultimate guide to becoming proficient in Python. This course covers everything you need to build a solid foundation from fundamental programming concepts to advanced techniques. With **hands-on projects**, real-world examples, and expert guidance, you'll gain the confidence to tackle complex **coding challenges**. Whether you're starting from scratch or aiming to enhance your skills, this course is the perfect fit. Enroll now and master Python, the language of the future!
