---
icon: material/graph-outline
---

# Graphs

Graphs in data structures are used to represent networks of connected elements, where the elements are called vertices (or nodes), and the connections between them are called edges. Graphs can be directed (where the edges have a direction) or undirected (where the edges do not have a direction). They can also be weighted (where edges have a weight or cost associated with them) or unweighted.

Here's a basic implementation of a graph in Python:

### 1. **Graph Representation**

Graphs can be represented in several ways, such as:

- **Adjacency Matrix:** A 2D array where each cell `(i, j)` indicates the presence of an edge between vertex `i` and vertex `j`.

- **Adjacency List:** A list where each element is a list of the neighbors (connected vertices) of a vertex.

- **Edge List:** A list of edges, where each edge is represented by a pair (or tuple) of vertices.

### 2. **Adjacency List Implementation**

Here’s a basic implementation using an adjacency list:

```python
class Graph:
    def __init__(self):
        self.graph = {}
    
    def add_vertex(self, vertex):
        if vertex not in self.graph:
            self.graph[vertex] = []
    
    def add_edge(self, vertex1, vertex2):
        if vertex1 in self.graph and vertex2 in self.graph:
            self.graph[vertex1].append(vertex2)
            self.graph[vertex2].append(vertex1)  # For undirected graph

    def display(self):
        for vertex, edges in self.graph.items():
            print(f"{vertex}: {edges}")

# Example usage
g = Graph()
g.add_vertex("A")
g.add_vertex("B")
g.add_vertex("C")
g.add_edge("A", "B")
g.add_edge("A", "C")
g.add_edge("B", "C")
g.display()
```

### 3. **Graph Traversal Algorithms**

- **Breadth-First Search (BFS):**

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

# Example usage
bfs(g.graph, "A")
```

- **Depth-First Search (DFS):**

```python
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    print(start, end=" ")
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

# Example usage
dfs(g.graph, "A")
```

### 4. **Weighted Graph Implementation**

To implement a weighted graph, you can modify the adjacency list to store weights:

```python
class WeightedGraph:
    def __init__(self):
        self.graph = {}
    
    def add_vertex(self, vertex):
        if vertex not in self.graph:
            self.graph[vertex] = []
    
    def add_edge(self, vertex1, vertex2, weight):
        if vertex1 in self.graph and vertex2 in self.graph:
            self.graph[vertex1].append((vertex2, weight))
            self.graph[vertex2].append((vertex1, weight))  # For undirected graph
    
    def display(self):
        for vertex, edges in self.graph.items():
            print(f"{vertex}: {edges}")

# Example usage
wg = WeightedGraph()
wg.add_vertex("A")
wg.add_vertex("B")
wg.add_vertex("C")
wg.add_edge("A", "B", 5)
wg.add_edge("A", "C", 10)
wg.add_edge("B", "C", 3)
wg.display()
```

### 5. **Applications of Graphs**

- Social networks

- Pathfinding algorithms (e.g., GPS systems)

- Networks (e.g., computer networks, electrical circuits)

- Web page ranking (e.g., Google's PageRank algorithm)

This is a basic overview of graph implementations in Python. You can expand on this to include more complex algorithms and data structures depending on your needs.
