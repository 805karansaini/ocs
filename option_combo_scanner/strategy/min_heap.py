import heapq


class MinHeap:
    def __init__(self):
        self.heap = []

    def push(self, item):
        heapq.heappush(self.heap, item)

    def push_multiple(self, items: list):
        for item in items:
            self.push(item)

    def pop(self):
        if self.heap:
            return heapq.heappop(self.heap)
        else:
            raise IndexError("pop from an empty heap")

    def peek(self):
        if self.heap:
            return self.heap[0]
        else:
            return None

    def update(self, old_item, new_item):
        try:
                
            self.heap[self.heap.index(old_item)] = new_item
            heapq.heapify(self.heap)
        except Exception as e:
            print(f"Min Heap Exception: {e}")

    def get_items(self):
        return sorted(self.heap)
    
    def __len__(self):
        return len(self.heap)
