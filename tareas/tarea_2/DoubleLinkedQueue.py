class Node:
	def __init__(self, value, prev=None, next=None) -> None:
		self.value = value
		self.prev = prev
		self.next = next


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
			node: Node = Node(elem, next=self.list)
			self.list.prev = node
			self.list = node
			self.size += 1
		else:
			self.list = Node(elem, next=self.list)
			self.last = self.last.prev
			self.last.next = None

	def pop(self):
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
		while (value := self.get(i)) is not None:
			l.append(value)
			i += 1
		return str(l)
