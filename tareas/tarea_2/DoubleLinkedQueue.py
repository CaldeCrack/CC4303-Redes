class Node:
	def __init__(self, value, prev=None, next=None) -> None:
		self.value = value
		self.prev = prev
		self.next = next


# First In First Out (FIFO)
class DoubleLinkedQueue:
	def __init__(self, limit: int) -> None:
		self.size = 0
		self.limit = limit
		self.list = None
		self.last = None

	def append(self, elem) -> None:
		if self.list is None:
			self.list = Node(elem)
			self.size = 1
			self.last = self.list
		elif self.size < self.limit:
			node: Node = Node(elem, prev=self.last)
			self.last.next = node
			self.last = node
			self.size += 1
		else:
			self.list.next.prev = None
			self.list = self.list.next
			self.last.next = Node(elem, prev=self.last)

	def pop(self):
		if self.size:
			value = self.list.value
			self.list = self.list.next
			self.size -= 1
			return value

	def get(self, index):
		if index == self.size:
			return None

		i: int = 0
		node: Node = self.list
		while i < index:
			i += 1
			node = node.next
		return node.value

	def __str__(self) -> str:
		l: list = []
		i: int = 0
		node: Node = self.list
		while node is not None:
			l.append(node.value)
			i += 1
			node = node.next
		return str(l)

dlq = DoubleLinkedQueue(4)
dlq.append(0)
print(dlq)
dlq.append(1)
print(dlq)
dlq.append(2)
print(dlq)
dlq.append(3)
print(dlq)
dlq.append(4)
print(dlq)
dlq.pop()
print(dlq)
dlq.pop()
print(dlq)
