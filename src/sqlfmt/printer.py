from typing import List

from sqlfmt.node import Node


def show_tree(node: Node) -> str:
    return " " * 4 * node.depth + node.value + show_children(node.children)


def show_children(nodes: List[Node]) -> str:
    if not nodes:
        return ""
    return "\n" + show_trees(nodes)


def show_trees(nodes: List[Node]) -> str:
    if len(nodes) == 1:
        return show_tree(nodes[0])
    else:
        return show_tree(nodes[0]) + "\n" + show_trees(nodes[1:])
