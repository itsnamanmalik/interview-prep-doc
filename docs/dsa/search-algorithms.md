---
icon: material/folder-search-outline
---

# Search Algorithms

Search algorithms are fundamental to computer science and are used to retrieve information stored in data structures like arrays, lists, trees, and graphs. Here are some common types of search algorithms, along with their Python implementations:

### 1. **Linear Search**

Linear search is the simplest search algorithm. It checks each element in the list one by one until it finds the target value.

- **Time Complexity:** `O(n)`

- **Best for:** Small or unsorted lists.

- **Speed:** Slow for large datasets.

**Python Implementation:**

```python
def linear_search(arr, target):
    for index, value in enumerate(arr):
        if value == target:
            return index
    return -1

# Example usage:
arr = [2, 4, 6, 8, 10]
target = 8
result = linear_search(arr, target)
print("Target found at index:", result)
```

### 2. **Binary Search**

Binary search is more efficient than linear search but requires the list to be sorted. It repeatedly divides the search interval in half and compares the target value to the middle element.

- **Time Complexity:** `O(log n)`

- **Best for:** Large, sorted lists.

- **Speed:** Fast, especially for large datasets.

**Python Implementation:**

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Example usage:
arr = [2, 4, 6, 8, 10]
target = 8
result = binary_search(arr, target)
print("Target found at index:", result)
```

### 3. **Depth-First Search (DFS)**

DFS is a graph traversal algorithm that explores as far as possible along a branch before backtracking. It's commonly used with stacks (or recursion).

- **Time Complexity:** `O(V + E)` where `V` is the number of vertices and `E` is the number of edges.

- **Best for:** Traversing or searching tree and graph structures.

- **Speed:** Depends on the structure; generally efficient for sparse graphs.

**Python Implementation:**

```python
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    print(start, end=" ")

    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

# Example usage:
graph = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [],
    'E': ['F'],
    'F': []
}
dfs(graph, 'A')
```

### 4. **Breadth-First Search (BFS)**

BFS is another graph traversal algorithm that explores all neighbors at the present depth before moving on to nodes at the next depth level. It's typically implemented using a queue.

- **Time Complexity:** `O(V + E)`

- **Best for:** Finding the shortest path in unweighted graphs.

- **Speed:** Similar to DFS; efficient for certain types of graphs.

**Python Implementation:**

```python
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)

    while queue:
        vertex = queue.popleft()
        print(vertex, end=" ")

        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

# Example usage:
graph = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [],
    'E': ['F'],
    'F': []
}
bfs(graph, 'A')
```

The speed of a search algorithm depends on the structure and characteristics of the data as well as the specific context in which the algorithm is used. Here's a comparison of the algorithms mentioned based on their time complexities:

### **Fastest Algorithm:**

- **Binary Search** and **Interpolation Search** are generally the fastest for large, sorted datasets. However, **Interpolation Search** can outperform **Binary Search** if the data is uniformly distributed.

- **Exponential Search** is also very efficient for very large or unbounded sorted datasets.

**Key Point:** **Binary Search** is often the go-to for most practical purposes due to its simplicity and efficiency. **Interpolation Search** can be faster, but only under specific conditions (uniformly distributed data).
