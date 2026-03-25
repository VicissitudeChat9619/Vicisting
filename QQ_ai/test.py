import queue

q = queue.Queue()

q.put(1)

q.put(10)

print(q.get())

print(list(q.queue))
