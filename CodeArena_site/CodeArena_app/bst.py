# Node

class BSTNode:
    def __init__(self, problem):
        self.problem = problem
        self.left = None
        self.right = None


# class

class ProblemBST:
    def __init__(self):
        self.root = None

    def insert(self, problem):
        if self.root is None:
            self.root = BSTNode(problem)
        else:
            self._insert(self.root, problem)

    def _insert(self, node, problem):
        if problem.title.lower() < node.problem.title.lower():
            if node.left is None:
                node.left = BSTNode(problem)
            else:
                self._insert(node.left, problem)
        else:
            if node.right is None:
                node.right = BSTNode(problem)
            else:
                self._insert(node.right, problem)

    def search(self, title):
        return self._search(self.root, title.lower())

    def _search(self, node, title):
        if node is None:
            return None

        node_title = node.problem.title.lower()

        if title == node_title:
            return node.problem

        if title < node_title:
            return self._search(node.left, title)

        return self._search(node.right, title)
    def search_partial(self, keyword):
        keyword = keyword.lower()
        results = []
        self._search_partial(self.root, keyword, results)
        return results


    def _search_partial(self, node, keyword, results):
        if not node:
            return

        title = node.problem.title.lower()

        # If keyword is inside title (even single letter)
        if keyword in title:
            results.append(node.problem)

        # Continue traversal
        self._search_partial(node.left, keyword, results)
        self._search_partial(node.right, keyword, results)

