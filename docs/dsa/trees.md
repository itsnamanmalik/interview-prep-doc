---
icon: material/file-tree
---

# Trees

A tree is a widely used data structure in computer science that simulates a hierarchical tree structure with a set of connected nodes. The most common type of tree is a binary tree, where each node has at most two children. Trees are used to represent hierarchical relationships and are fundamental in various algorithms and applications like search engines, file systems, and database indexing.

### 1. **Basic Terminology**

- **Node:** The basic unit of a tree, containing data and possibly links to other nodes.

- **Root:** The topmost node of the tree.

- **Leaf:** A node that does not have any children.

- **Parent:** A node that has one or more children.

- **Child:** A node that is a descendant of another node.

- **Subtree:** A tree consisting of a node and its descendants.

### 2. **Binary Tree Implementation**

Here’s a basic implementation of a binary tree in Python:

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, data):
        if self.root is None:
            self.root = Node(data)
        else:
            self._insert(self.root, data)

    def _insert(self, node, data):
        if data < node.data:
            if node.left is None:
                node.left = Node(data)
            else:
                self._insert(node.left, data)
        else:
            if node.right is None:
                node.right = Node(data)
            else:
                self._insert(node.right, data)

    def inorder_traversal(self, node, result=None):
        if result is None:
            result = []
        if node:
            self.inorder_traversal(node.left, result)
            result.append(node.data)
            self.inorder_traversal(node.right, result)
        return result

    def preorder_traversal(self, node, result=None):
        if result is None:
            result = []
        if node:
            result.append(node.data)
            self.preorder_traversal(node.left, result)
            self.preorder_traversal(node.right, result)
        return result

    def postorder_traversal(self, node, result=None):
        if result is None:
            result = []
        if node:
            self.postorder_traversal(node.left, result)
            self.postorder_traversal(node.right, result)
            result.append(node.data)
        return result

# Example usage
bt = BinaryTree()
bt.insert(10)
bt.insert(5)
bt.insert(20)
bt.insert(3)
bt.insert(7)

print("Inorder Traversal:", bt.inorder_traversal(bt.root))
print("Preorder Traversal:", bt.preorder_traversal(bt.root))
print("Postorder Traversal:", bt.postorder_traversal(bt.root))
```

### 3. **Tree Traversal Methods**

- **Inorder Traversal (Left, Root, Right):**

    - This traversal method visits the left subtree, the root node, and then the right subtree.

- **Preorder Traversal (Root, Left, Right):**

    - This traversal method visits the root node first, then the left subtree, and finally the right subtree.

- **Postorder Traversal (Left, Right, Root):**

    - This traversal method visits the left subtree, the right subtree, and finally the root node.

### 4. **Binary Search Tree (BST)**

A Binary Search Tree (BST) is a type of binary tree where the left child of a node contains only nodes with values less than the parent node, and the right child contains only nodes with values greater than the parent node.

The above `BinaryTree` class can be considered a Binary Search Tree (BST) due to its insertion logic.

### 5. **Balanced Trees**

Balanced trees like AVL trees or Red-Black trees maintain a balanced height to ensure that operations like insertion, deletion, and search are done in O(log n) time. These trees require more complex insertion and deletion algorithms to maintain balance.

### 6. **Applications of Trees**

- **Binary Search Trees:** Efficient searching, insertion, and deletion operations.

- **Heaps:** Used in priority queues and for implementing efficient sorting algorithms like Heap Sort.

- **Trie:** Efficient storage and retrieval of strings, used in autocomplete systems.

- **Expression Trees:** Used to represent arithmetic expressions.

- **File Systems:** Hierarchical organization of files and directories.

This implementation can be extended to more complex tree structures like AVL trees, B-trees, etc., depending on the requirements.
