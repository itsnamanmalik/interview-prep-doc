---
icon: material/bandage
---

# Monkey Patching

**Monkey patching** means replacing an attribute — usually a function or method — on a class or module *at run time*, after it has already been defined and imported. The original source file is never touched; the change lives only in memory for the life of the process.

It is possible because classes and modules in Python are ordinary mutable objects. Their attributes live in a dictionary, and nothing stops you from reassigning an entry after import.

### Basic Example

```python
class GeeksClass:
    def function(self):
        print("function()")

def monkey_function(self):
    print("monkey_function()")


GeeksClass.function = monkey_function
obj = GeeksClass()
obj.function()
```

Output:

```
monkey_function()
```

The class object simply had its `function` entry overwritten. Note that the replacement still has to accept `self`, because it is being installed as a method on the class.

### Patching a Class Affects Existing Instances

Attribute lookup happens on every call, not once at construction. So instances created *before* the patch pick it up too:

```python
class Service:
    def ping(self):
        return "pong"

before = Service()

Service.ping = lambda self: "patched"

after = Service()

print(before.ping())  # patched
print(after.ping())   # patched
```

This is the property that makes monkey patching powerful, and also the reason it is easy to cause action at a distance: one line changes behaviour for every user of that class in the whole process.

### Patching a Single Instance

To affect one object only, set the attribute on the instance rather than the class. There is a catch — a plain function assigned to an instance is **not** turned into a bound method, so it receives no `self`:

```python
class Service:
    def ping(self):
        return "pong"

a, b = Service(), Service()

# No self is passed: this is just an attribute that happens to be callable.
a.ping = lambda: "only a"

print(a.ping())  # only a
print(b.ping())  # pong
```

If the replacement needs `self`, bind it explicitly with `types.MethodType`:

```python
import types

class Service:
    def ping(self):
        return f"only {self.name}"

    name = "a"

a, b = Service(), Service()
a.ping = types.MethodType(lambda self: f"patched {self.name}", a)

print(a.ping())  # patched a
print(b.ping())  # only a
```

The descriptor protocol is what normally does this binding for you when a function is looked up on a *class*; assigning to an instance skips it entirely.

### Patching a Module-Level Function

The same idea applies to modules. Keep a reference to the original so you can wrap it rather than lose it:

```python
import json

original_dumps = json.dumps

def loud_dumps(*args, **kwargs):
    print("serialising...")
    return original_dumps(*args, **kwargs)

json.dumps = loud_dumps

print(json.dumps({"a": 1}))

json.dumps = original_dumps  # always restore
```

Output:

```
serialising...
{"a": 1}
```

!!! warning "Patch the attribute, not the import"
    `from json import dumps` copies the function into your module's namespace. Patching `json.dumps` afterwards will **not** affect that local name — it still points at the original. Patch where the name is *looked up*, which is why `import json` then `json.dumps(...)` is the patchable style.

### Restoring Safely with a Context Manager

An unrestored patch leaks into everything that runs later in the process, which is a common source of test pollution. Scope it:

```python
from contextlib import contextmanager

@contextmanager
def patched(obj, name, replacement):
    original = getattr(obj, name)
    setattr(obj, name, replacement)
    try:
        yield
    finally:
        setattr(obj, name, original)


class Clock:
    def now(self):
        return "real time"

with patched(Clock, "now", lambda self: "2026-01-01"):
    print(Clock().now())  # 2026-01-01

print(Clock().now())      # real time
```

The `try`/`finally` matters: without it, an exception inside the block would leave the patch in place.

### The Disciplined Version: `unittest.mock.patch`

In tests you rarely need to hand-roll any of this. The standard library already provides patching that restores itself and records calls:

```python
from unittest.mock import patch

class PaymentGateway:
    def charge(self, amount):
        raise RuntimeError("real network call")

def checkout(gateway, amount):
    return gateway.charge(amount)


with patch.object(PaymentGateway, "charge", return_value="ok") as fake_charge:
    print(checkout(PaymentGateway(), 100))   # ok
    fake_charge.assert_called_once_with(100)

# Outside the block the real method is back.
```

`patch` also works as a decorator (`@patch("myapp.services.charge")`) and takes `autospec=True`, which makes the replacement enforce the original signature — worth mentioning in an interview, because a mock with the wrong signature will happily let a broken call pass.

### When It Is Reasonable

- **Testing.** Replacing network, clock, filesystem or payment calls with predictable stand-ins. This is by far the most common legitimate use.

- **Fixing a third-party bug you cannot wait on.** A targeted patch can unblock a release while an upstream fix is pending. Leave a comment with a link to the issue and delete it once the dependency is upgraded.

- **Instrumentation.** Wrapping a library function to add timing, logging or metrics without forking it.

### Why It Is Risky

- **Invisible.** The patch lives far away from the code it changes. Someone reading `Service.ping` in the source sees the original body and no hint that it was replaced.

- **Fragile across upgrades.** You are depending on a private-ish implementation detail: a method name, its signature, the module it lives in. A minor version bump can silently break the patch or make it a no-op.

- **Order-dependent.** The patch only applies once the patching code has been imported and executed. Anything that ran earlier used the original.

- **Process-wide and not thread-safe.** There is one class object shared by every thread; patching it mid-flight affects work already in progress.

- **Only one winner.** Two libraries patching the same method will silently clobber each other, and the outcome depends on import order.

### Alternatives Worth Reaching For First

| Instead of patching | Consider | Why |
| --- | --- | --- |
| Replacing a method globally | **Subclassing** and overriding | Explicit, discoverable, scoped to the subclass |
| Wrapping a function to add behaviour | A **decorator** | The change is visible at the definition site |
| Swapping a collaborator in tests | **Dependency injection** | Pass the fake in; no global state to restore |
| Extending behaviour you own | **Composition** | Keeps the modification local and testable |

Monkey patching is the right answer when you do not control the code and cannot change the call site. When you do control it, one of the options above is almost always clearer.

### Interview Summary

> Monkey patching is run-time replacement of an attribute on a class or module, made possible by Python's mutable class and module namespaces. Its legitimate home is testing, where `unittest.mock.patch` provides it with automatic restoration. Outside tests it trades clarity for reach: the change is global, invisible at the point of use, and coupled to another project's internals — so prefer subclassing, decorators or dependency injection whenever the call site is yours to change.
