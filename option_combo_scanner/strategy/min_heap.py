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

    def delete_item(self, config_id):
        try:
            for item in self.heap:
                if item[1] == config_id:
                    self.heap.remove(item)
                    heapq.heapify(self.heap)
                    return
            # If config_id is not found in any item
            raise ValueError("Configuration ID not found in heap")
        except ValueError as e:
            print(f"Min Heap Exception: {e}")

    def get_items(self):
        return sorted(self.heap)

    def __len__(self):
        return len(self.heap)

    def __str__(self):
        return ", ".join(map(str, self.heap))
