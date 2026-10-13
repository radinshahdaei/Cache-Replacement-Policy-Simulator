import csv

class Node:
    def __init__(self, content):
        self.content = content
        self.left = None
        self.right = None
        self.parent = None
        self.height = 1
        self.subtreeSize = 1


class Tree:
    def __init__(self):
        self.root = None
        self.nodeMap = {}  # Hash table to map content to tree nodes

    def insert(self, content):
        """Insert a new node with the given content into the tree."""
        newNode = Node(content)
        self.nodeMap[content] = newNode
        if self.root is None:
            self.root = newNode
        else:
            self.insertLeftMost(newNode)
        self.updateTreeFromNode(newNode)

    def delete(self, content):
        """Delete the node with the given content from the tree."""
        if content not in self.nodeMap:
            raise ValueError("Content not found in the tree")
        nodeToDelete = self.nodeMap.pop(content)
        self.deleteNode(nodeToDelete)

    def getRank(self, content):
        """Return the rank (index) of the node with the given content."""
        if content not in self.nodeMap:
            raise ValueError("Content not found in the tree")
        node = self.nodeMap[content]
        return self.calculateRank(node)

    def insertLeftMost(self, node):
        """Insert the node at the leftmost position."""
        current = self.root
        while current.left is not None:
            current = current.left
        current.left = node
        node.parent = current

    def deleteNode(self, node):
        """Delete the given node from the tree."""
        if node.left is None and node.right is None:
            self.unlinkNode(node)
        elif node.left is None:
            self.replaceNode(node, node.right)
        elif node.right is None:
            self.replaceNode(node, node.left)
        else:
            successor = self.findLeftmost(node.right)
            node.content = successor.content
            self.nodeMap[successor.content] = node
            self.deleteNode(successor)
        self.updateTreeFromNode(node.parent)

    def unlinkNode(self, node):
        """Unlink the given node from the tree."""
        if node.parent is None:
            self.root = None
        elif node == node.parent.left:
            node.parent.left = None
        else:
            node.parent.right = None

    def replaceNode(self, node, replacement):
        """Replace the given node with the replacement node."""
        if node.parent is None:
            self.root = replacement
        elif node == node.parent.left:
            node.parent.left = replacement
        else:
            node.parent.right = replacement
        replacement.parent = node.parent

    def findLeftmost(self, node):
        """Find the leftmost (minimum) node in the subtree rooted at the given node."""
        while node.left is not None:
            node = node.left
        return node

    def updateTreeFromNode(self, node):
        """Update the tree from the given node upwards to the root."""
        while node is not None:
            self.updateNodeSizeAndHeight(node)
            self.balanceTree(node)
            node = node.parent

    def updateNodeSizeAndHeight(self, node):
        """Update the size and height of the given node."""
        node.subtreeSize = 1 + self.getSize(node.left) + self.getSize(node.right)
        node.height = 1 + max(self.getHeight(node.left), self.getHeight(node.right))

    def balanceTree(self, node):
        """Balance the tree from the given node upwards to the root."""
        while node is not None:
            balance = self.getBalance(node)
            if balance > 1:
                if self.getBalance(node.left) < 0:
                    node.left = self.rotateLeft(node.left)
                node = self.rotateRight(node)
            elif balance < -1:
                if self.getBalance(node.right) > 0:
                    node.right = self.rotateRight(node.right)
                node = self.rotateLeft(node)
            self.updateNodeSizeAndHeight(node)
            node = node.parent

    def getBalance(self, node):
        """Get the balance factor of the given node."""
        return self.getHeight(node.left) - self.getHeight(node.right)

    def rotateLeft(self, node):
        """Perform a left rotation on the given node."""
        newRoot = node.right
        node.right = newRoot.left
        if newRoot.left is not None:
            newRoot.left.parent = node
        self.relinkParent(node, newRoot)
        newRoot.left = node
        node.parent = newRoot
        self.updateNodeSizeAndHeight(node)
        self.updateNodeSizeAndHeight(newRoot)
        return newRoot

    def rotateRight(self, node):
        """Perform a right rotation on the given node."""
        newRoot = node.left
        node.left = newRoot.right
        if newRoot.right is not None:
            newRoot.right.parent = node
        self.relinkParent(node, newRoot)
        newRoot.right = node
        node.parent = newRoot
        self.updateNodeSizeAndHeight(node)
        self.updateNodeSizeAndHeight(newRoot)
        return newRoot

    def relinkParent(self, oldNode, newNode):
        """Relink the parent of the old node to the new node."""
        newNode.parent = oldNode.parent
        if oldNode.parent is None:
            self.root = newNode
        elif oldNode.parent.left == oldNode:
            oldNode.parent.left = newNode
        else:
            oldNode.parent.right = newNode

    def getSize(self, node):
        """Get the size of the subtree rooted at the given node."""
        return node.subtreeSize if node else 0

    def getHeight(self, node):
        """Get the height of the given node."""
        return node.height if node else 0

    def calculateRank(self, node):
        """Calculate the rank (index) of the given node."""
        rank = self.getSize(node.left)
        while node.parent is not None:
            if node == node.parent.right:
                rank += self.getSize(node.parent.left) + 1
            node = node.parent
        return rank


def calculate_reuse_distance(traceFile):
    tree = Tree()
    last_occurrence = {}
    reuse_distances = initialize_reuse_distances()
    no_reuse_data = 0

    with open(traceFile, "r") as file:
        rows = file.readlines()
        for i, row in enumerate(rows):
            _, _, offset, _, _, _, _, _ = row.strip().split(",")
            if offset in last_occurrence:
                no_reuse_data += 1
                last_index = last_occurrence[offset]
                rank = tree.getRank(last_index)
                update_reuse_distance(rank, reuse_distances)
                tree.delete(last_index)
            last_occurrence[offset] = i
            tree.insert(i)

    if no_reuse_data > 0:
        reuse_distances["avg"] /= no_reuse_data
    return reuse_distances


def initialize_reuse_distances():
    """Initialize the reuse distances dictionary with appropriate keys and default values."""
    reuse_distances = {"avg": 0, "min": float("inf"), "max": -1, "0": 0, ">128K": 0}
    index = 1
    while index < 256 * 1024:
        if index < 1024:
            reuse_distances[str(index)] = 0
        else:
            temp = index // 1024
            reuse_distances[str(temp) + "K"] = 0
        index *= 2
    return reuse_distances


def update_reuse_distance(rank, reuse_distances):
    """Update the reuse distances based on the given rank."""
    reuse_distances["avg"] += rank
    reuse_distances["min"] = min(reuse_distances["min"], rank)
    reuse_distances["max"] = max(reuse_distances["max"], rank)

    # Special case for ranks > 128K
    if rank > 128 * 1024:
        reuse_distances[">128K"] += 1
        return

    # List of thresholds for reuse distances
    thresholds = [
        (0, "0"),
        (1, "1"),
        (2, "2"),
        (4, "4"),
        (8, "8"),
        (16, "16"),
        (32, "32"),
        (64, "64"),
        (128, "128"),
        (256, "256"),
        (512, "512"),
        (1024, "1.0K"),
        (2048, "2.0K"),
        (4096, "4.0K"),
        (8192, "8.0K"),
        (16384, "16.0K"),
        (32768, "32.0K"),
        (65536, "64.0K"),
        (131072, "128.0K"),
    ]

    # Update the appropriate bucket
    for threshold, label in thresholds:
        if rank <= threshold:
            reuse_distances[label] += 1
            return

def add_to_output(traceFile, reuse_distances):
    data_list = [traceFile]
    for key in reuse_distances.keys():
        data_list.append(reuse_distances[key])
    with open("output.csv", "a", newline="") as outFile:
        writer = csv.writer(outFile)
        writer.writerow(data_list)

traceFile = "input.csv"
reuse_distances = calculate_reuse_distance(traceFile)
add_to_output(traceFile, reuse_distances)