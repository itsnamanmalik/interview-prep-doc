---
icon: material/lock
---

# Centralised Locking

**Central Coordinator**: A single entity manages and coordinates access to the shared resource.

**Request and Grant Mechanism**: Processes or threads request access from the central coordinator, which grants or denies access based on current state.

**Mutual Exclusion**: Ensures only one process or thread can access the resource at a time.

**Single Point of Control**: Simplifies management but introduces a potential bottleneck.

**Scalability Concerns**: Can become a performance bottleneck or single point of failure with high request volume.

**Use Cases**: Common in distributed systems, databases, and file systems to manage access to critical sections.
