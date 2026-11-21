"""Search algorithms used by the Ghost AI: Breadth-First Search and A*.

Both return (path, nodes_expanded). `path` runs from start to goal inclusive
([] if the goal cannot be reached). `nbrs` is a function: tile -> neighbour tiles.

`banned_first` is the tile the ghost just came from. Ghosts are not allowed to
turn around on the spot, so that tile is skipped as the FIRST step (unless it is
the only way out of a dead end).
"""
import heapq
from collections import deque

from maze_hunter.core.maze import manhattan


def _first_steps(start, nbrs, banned_first):
    moves = list(nbrs(start))
    allowed = [n for n in moves if n != banned_first]
    return allowed or moves


def _rebuild(parent, goal):
    path = [goal]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def bfs(start, goal, nbrs, banned_first=None):
    """Breadth-First Search: explores the maze level by level.

    Every move costs 1, so the first time BFS reaches the goal it has found a
    shortest path. It has no sense of direction, so it explores in all directions.
    """
    if start == goal:
        return [start], 0
    parent = {start: None}
    queue = deque()
    for n in _first_steps(start, nbrs, banned_first):
        parent[n] = start
        queue.append(n)
    expanded = 1
    while queue:
        cur = queue.popleft()
        expanded += 1
        if cur == goal:
            return _rebuild(parent, goal), expanded
        for n in nbrs(cur):
            if n not in parent:
                parent[n] = cur
                queue.append(n)
    return [], expanded


def astar(start, goal, nbrs, banned_first=None):
    """A* search: f(n) = g(n) + h(n).

    g(n) = steps taken so far, h(n) = Manhattan distance to the goal.
    Manhattan distance never overestimates on a 4-direction grid, so A* still
    returns a shortest path, but it expands far fewer tiles than BFS because it
    looks toward the goal first.
    """
    if start == goal:
        return [start], 0
    g = {start: 0}
    parent = {start: None}
    heap = []
    counter = 0
    for n in _first_steps(start, nbrs, banned_first):
        g[n] = 1
        parent[n] = start
        h = manhattan(n, goal)
        heapq.heappush(heap, (1 + h, h, counter, n))
        counter += 1
    closed = {start}
    expanded = 1
    while heap:
        _, _, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if cur == goal:
            return _rebuild(parent, goal), expanded
        for n in nbrs(cur):
            if n in closed:
                continue
            ng = g[cur] + 1
            if n not in g or ng < g[n]:
                g[n] = ng
                parent[n] = cur
                h = manhattan(n, goal)
                heapq.heappush(heap, (ng + h, h, counter, n))
                counter += 1
    return [], expanded