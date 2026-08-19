---
icon: material/sort
---

# Sorting Algorithms

### 1. **Bubble Sort**

- **Explanation:**

    - Repeatedly swaps adjacent elements if they are in the wrong order.

    - Simple but inefficient for large datasets.

    - Time Complexity: `O(n^2)`

**Python Implementation:**

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Example usage:
arr = [64, 34, 25, 12, 22, 11, 90]
print(bubble_sort(arr))
```

### 2. **Selection Sort**

- **Explanation:**

    - Selects the smallest (or largest) element and swaps it with the first unsorted element.

    - Simple but not suitable for large datasets.

    - Time Complexity: `O(n^2)`

**Python Implementation:**

```python
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

# Example usage:
arr = [64, 25, 12, 22, 11]
print(selection_sort(arr))
```

### 3. **Insertion Sort**

- **Explanation:**

    - Builds a sorted array one element at a time by repeatedly picking the next element and inserting it into the correct position.

    - Efficient for small or partially sorted datasets.

    - Time Complexity: `O(n^2)`

**Python Implementation:**

```python
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

# Example usage:
arr = [12, 11, 13, 5, 6]
print(insertion_sort(arr))
```

### 4. **Merge Sort**

- **Explanation:**

    - Divides the array into halves, recursively sorts each half, and merges them back together.

    - Efficient and stable.

    - Time Complexity: `O(n log n)`

**Python Implementation:**

```python
def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left_half = arr[:mid]
        right_half = arr[mid:]

        merge_sort(left_half)
        merge_sort(right_half)

        i = j = k = 0

        while i < len(left_half) and j < len(right_half):
            if left_half[i] < right_half[j]:
                arr[k] = left_half[i]
                i += 1
            else:
                arr[k] = right_half[j]
                j += 1
            k += 1

        while i < len(left_half):
            arr[k] = left_half[i]
            i += 1
            k += 1

        while j < len(right_half):
            arr[k] = right_half[j]
            j += 1
            k += 1

    return arr

# Example usage:
arr = [38, 27, 43, 3, 9, 82, 10]
print(merge_sort(arr))
```

### 5. **Quick Sort**

- **Explanation:**

    - Selects a 'pivot' element, partitions the array around the pivot, and recursively sorts the partitions.

    - Efficient for large datasets but not stable.

    - Time Complexity: `O(n log n)` on average.

**Python Implementation:**

```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Example usage:
arr = [10, 7, 8, 9, 1, 5]
print(quick_sort(arr))
```

### 6. **Heap Sort**

- **Explanation:**

    - Converts the array into a heap structure, repeatedly extracts the maximum element, and rebuilds the heap.

    - Efficient and works well for large datasets.

    - Time Complexity: `O(n log n)`

**Python Implementation:**

```python
def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    if left < n and arr[i] < arr[left]:
        largest = left

    if right < n and arr[largest] < arr[right]:
        largest = right

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)

def heap_sort(arr):
    n = len(arr)

    for i in range(n//2, -1, -1):
        heapify(arr, n, i)

    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0)

    return arr

# Example usage:
arr = [12, 11, 13, 5, 6, 7]
print(heap_sort(arr))
```

### 7. **Counting Sort**

- **Explanation:**

    - Counts the number of occurrences of each distinct element and uses this count to place elements in the sorted order.

    - Efficient for small range integer data.

    - Time Complexity: `O(n + k)`, where `k` is the range of the input.

**Python Implementation:**

```python
def counting_sort(arr):
    max_val = max(arr)
    count = [0] * (max_val + 1)

    for num in arr:
        count[num] += 1

    sorted_arr = []
    for i, c in enumerate(count):
        sorted_arr.extend([i] * c)

    return sorted_arr

# Example usage:
arr = [4, 2, 2, 8, 3, 3, 1]
print(counting_sort(arr))
```

### 8. **Radix Sort**

- **Explanation:**

    - Sorts numbers by processing individual digits. Uses counting sort as a subroutine.

    - Efficient for sorting large numbers.

    - Time Complexity: `O(d * (n + k))`, where `d` is the number of digits.

**Python Implementation:**

```python
def counting_sort_for_radix(arr, exp):
    n = len(arr)
    output = [0] * n
    count = [0] * 10

    for i in range(n):
        index = arr[i] // exp
        count[index % 10] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    i = n - 1
    while i >= 0:
        index = arr[i] // exp
        output[count[index % 10] - 1] = arr[i]
        count[index % 10] -= 1
        i -= 1

    for i in range(len(arr)):
        arr[i] = output[i]

def radix_sort(arr):
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        counting_sort_for_radix(arr, exp)
        exp *= 10
    return arr

# Example usage:
arr = [170, 45, 75, 90, 802, 24, 2, 66]
print(radix_sort(arr))
```

These sorting algorithms cover a wide range of use cases, from small to large datasets, simple to complex structures, and integer to general data types. Each algorithm has its strengths and is suited for different scenarios.

### **Key Point:**

For general-purpose sorting, **Quick Sort** is often the fastest, especially for large datasets. However, **Counting Sort** and **Radix Sort** can outperform it in specific scenarios involving integers.
