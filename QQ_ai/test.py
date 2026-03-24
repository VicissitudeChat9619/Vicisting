import random


# random.randint(a, b)
class RandomizedSet:

    def __init__(self):
        self.arr = []
        self.k = dict()

    def insert(self, val: int) -> bool:
        if val not in self.k or self.k[val] == -1:
            self.arr.append(val)
            self.k[val] = len(self.arr) - 1
            return True
        return False

    def remove(self, val: int) -> bool:
        if val in self.k:
            self.k[self.arr[-1]] = self.k[val]
            self.arr[-1], self.arr[self.k[val]] = self.arr[self.k[val]], self.arr[-1]
            self.k[val] = -1
            self.arr.pop()
            return True
        return False

    def getRandom(self) -> int:
        index = random.randint(0, len(self.arr) - 1)
        return self.arr[index]


# Your RandomizedSet object will be instantiated and called as such:
obj = RandomizedSet()
obj.insert(0)
print(obj.arr)
obj.insert(1)
print(obj.arr)
obj.remove(0)
print(obj.arr)
obj.insert(2)
print(obj.arr)
obj.remove(1)
print(obj.arr)
print(obj.getRandom())
# param_3 = obj.getRandom()
