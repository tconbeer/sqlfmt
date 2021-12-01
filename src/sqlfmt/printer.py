from dataclasses import dataclass
from typing import Iterable, List, Union

from sqlfmt.node import Node
from sqlfmt.token import TokenType


@dataclass(frozen=True)
class TextLine:
    nodes: List[Node]
    depth: int

    def __repr__(self) -> str:
        return (
            f"TextLine(nodes={[str(node) for node in self.nodes]}, depth={self.depth})"
        )

    def __str__(self) -> str:
        if not self.nodes:
            return ""
        else:
            contents = [str(n) for n in self.nodes]
            contents[0].lstrip()
            return "".join(contents)

    def __len__(self) -> int:
        return len(str(self))


@dataclass(frozen=True)
class NilDoc:
    def __str__(self) -> str:
        return ""

    def __len__(self) -> int:
        return 0


@dataclass(frozen=True)
class LineDoc:
    depth: int

    def __str__(self) -> str:
        indent = " " * 4 * self.depth
        return "\n" + indent

    def __len__(self) -> int:
        return 0


@dataclass(frozen=True)
class SimpleDoc:
    text: Union[TextLine, str]

    def __str__(self) -> str:
        return str(self.text)

    def __len__(self) -> int:
        return len(self.text)


def simple_doc_from_nodes(nodes: List[Node]) -> Union[NilDoc, SimpleDoc]:
    if not nodes:
        return NilDoc()
    elif len(nodes) == 1 and nodes[0].token.type == TokenType.ROOT:
        return NilDoc()
    else:
        line = TextLine(nodes=nodes, depth=nodes[0].depth)
        return SimpleDoc(text=line)


@dataclass(frozen=True)
class UnionedDoc:
    x: "Doc"
    y: "Doc"

    def __iter__(self) -> "UnionedDoc":
        return self

    def __next__(self) -> Iterable["Doc"]:
        for d in [self.x, self.y]:
            if isinstance(d, UnionedDoc):
                yield from d
            else:
                yield d
        return


@dataclass(frozen=True)
class ConcatDoc:
    first: "Doc"
    second: "Doc"

    def __str__(self) -> str:
        # todo: handle prefix of second correctly
        return str(self.first) + str(self.second)

    def __len__(self) -> int:
        return len(str(self))


Doc = Union[NilDoc, SimpleDoc, LineDoc, ConcatDoc, UnionedDoc]
PureDoc = Union[NilDoc, SimpleDoc, LineDoc, ConcatDoc]


def concatenate(first: Doc, second: Doc) -> Doc:
    if isinstance(first, NilDoc):
        return second
    elif isinstance(second, NilDoc):
        return first
    elif isinstance(first, SimpleDoc) and isinstance(second, SimpleDoc):
        nodes: List[Node] = []
        if isinstance(first.text, TextLine):
            nodes = nodes + first.text.nodes
        if isinstance(second.text, TextLine):
            nodes = nodes + second.text.nodes
        return simple_doc_from_nodes(nodes=nodes)
    else:
        return ConcatDoc(first=first, second=second)


class CannotFlattenException(Exception):
    pass


def flatten(doc: Doc) -> Doc:
    if isinstance(doc, NilDoc):
        return doc
    elif isinstance(doc, ConcatDoc):
        return concatenate(first=flatten(doc.first), second=flatten(doc.second))
    elif isinstance(doc, SimpleDoc):
        return doc
    elif isinstance(doc, LineDoc):
        return NilDoc()
    elif isinstance(doc, UnionedDoc):
        return flatten(doc.x)  # all docs in a unioned set must flatten to same doc


class UnionInvariantError(Exception):
    pass


def doc_union(longer: Doc, shorter: Doc) -> Doc:
    # TODO: ensure all docs flatten to same doc?
    # TODO: ENFORCE length variant?
    # if isinstance(longer, UnionedDoc):
    #     shortest_long = min([len(x) for x in longer])
    # else:
    #     shortest_long = len(longer)

    # if isinstance(shorter, UnionedDoc):
    #     longest_short = max([len(x) for x in shorter])
    # else:
    #     longest_short = len(shorter)

    # if shortest_long < longest_short:
    #     raise UnionInvariantError
    # else:
    return UnionedDoc(x=longer, y=shorter)


def group(doc: Doc) -> Doc:
    if isinstance(doc, NilDoc) or isinstance(doc, SimpleDoc):
        return doc
    elif isinstance(doc, ConcatDoc):
        if isinstance(doc.first, SimpleDoc):
            return concatenate(first=doc.first, second=group(doc.second))
        elif isinstance(doc.first, ConcatDoc):
            return concatenate(first=group(doc.first), second=group(doc.second))
        elif isinstance(doc.first, LineDoc):
            return UnionedDoc(flatten(doc.second), doc)
        elif isinstance(doc.first, NilDoc):
            raise NotImplementedError
        elif isinstance(doc.first, UnionedDoc):
            raise NotImplementedError
    elif isinstance(doc, UnionedDoc):
        return UnionedDoc(group(doc.x), doc.y)
    else:
        raise NotImplementedError


def best(w: int, k: int, doc_parts: List[Doc]) -> PureDoc:
    """
    Takes a Doc (optionally split into a list of parts) that can contain unions
    and return a single Doc that cannot contain unions and that best fits
    the desired line width
    w: desired line width
    k: amount of line already used up before printing x or y
    """
    if not doc_parts:
        return NilDoc()
    elif isinstance(doc_parts[0], NilDoc):
        return best(w, k, doc_parts[1:])
    elif isinstance(doc_parts[0], ConcatDoc):
        return best(w, k, [doc_parts[0].first, doc_parts[0].second] + doc_parts[1:])
    elif isinstance(doc_parts[0], SimpleDoc):
        cat = concatenate(
            first=doc_parts[0],
            second=best(w, k + len(doc_parts[0]), doc_parts[1:]),
        )
        if isinstance(cat, UnionedDoc):
            raise TypeError
        else:
            return cat
    elif isinstance(doc_parts[0], LineDoc):
        cat = concatenate(
            first=doc_parts[0],
            second=best(w, k + doc_parts[0].depth * 4, doc_parts[1:]),
        )
        if isinstance(cat, UnionedDoc):
            raise TypeError
        else:
            return cat
    elif isinstance(doc_parts[0], UnionedDoc):
        return better(
            w,
            k,
            x=best(w, k, [doc_parts[0].x] + doc_parts[1:]),
            y=best(w, k, [doc_parts[0].y] + doc_parts[1:]),
        )


def better(w: int, k: int, x: PureDoc, y: PureDoc) -> PureDoc:
    """
    Returns the better of two documents (that don't contain unions), x and y.
    Assumes the lines in x are longer than the lines in y.
    w: desired line width
    k: amount of line already used up before printing x or y
    """
    better_doc = x if fits(w - k, x) else y
    return better_doc


def fits(w: int, x: PureDoc) -> bool:
    return len(x) <= w


###############################################


def pretty(w: int, node: Node) -> str:
    breakpoint()
    doc = show_tree(nodes=[node])
    breakpoint()
    return str(best(w=88, k=0, doc_parts=[doc])) + "\n"


def show_tree(nodes: List[Node]) -> Doc:
    if not nodes:
        return NilDoc()
    doc = group(
        concatenate(
            first=simple_doc_from_nodes(nodes),
            second=show_children(nodes[-1].children),
        )
    )
    return doc


def show_children(nodes: List[Node]) -> Doc:
    if not nodes:
        return NilDoc()
    else:
        return concatenate(LineDoc(depth=nodes[0].depth), group(show_trees(nodes)))


def show_trees(nodes: List[Node]) -> Doc:
    if len(nodes) == 1:
        return show_tree(nodes)
    else:
        head: List[Node] = []
        for node in nodes:
            if node.prefix == "" or not head:
                head.append(node)
                if node.children:
                    break
            else:
                break
        tail = nodes[len(head) :]
        if not tail:
            return show_tree(head)
        else:
            tail_doc = concatenate(
                first=LineDoc(depth=tail[0].depth), second=show_trees(tail)
            )
            return concatenate(first=show_tree(head), second=tail_doc)


###########
