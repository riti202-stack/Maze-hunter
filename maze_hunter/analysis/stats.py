"""Measurements for the AI vs AI evaluation and the A* vs BFS comparison."""
import csv
import random
import time

from maze_hunter.ai.search import astar, bfs


class SearchStats:
    """Counts calls, expanded nodes and time for each algorithm in one match."""
    ALGOS = ("A*", "BFS", "Minimax")

    def __init__(self):
        self.calls = {a: 0 for a in self.ALGOS}
        self.nodes = {a: 0 for a in self.ALGOS}
        self.seconds = {a: 0.0 for a in self.ALGOS}

    def record(self, algo, nodes, seconds):
        self.calls[algo] += 1
        self.nodes[algo] += nodes
        self.seconds[algo] += seconds

    def avg_nodes(self, algo):
        return self.nodes[algo] / self.calls[algo] if self.calls[algo] else 0.0

    def avg_ms(self, algo):
        return 1000 * self.seconds[algo] / self.calls[algo] if self.calls[algo] else 0.0


def match_summary(game, index):
    s = game.stats
    return {
        "match": index,
        "result": game.result,
        "score": game.score,
        "level": game.level,
        "lives_left": game.lives,
        "time_s": round(game.elapsed, 1),
        "minimax_avg_nodes": round(s.avg_nodes("Minimax"), 1),
        "minimax_avg_ms": round(s.avg_ms("Minimax"), 3),
        "astar_avg_nodes": round(s.avg_nodes("A*"), 1),
        "bfs_avg_nodes": round(s.avg_nodes("BFS"), 1),
    }


class BatchResults:
    """Results of a series of AI vs AI matches."""

    def __init__(self, total):
        self.total = total
        self.rows = []

    def add(self, game):
        self.rows.append(match_summary(game, len(self.rows) + 1))

    @property
    def done(self):
        return len(self.rows) >= self.total

    def count(self, result):
        return sum(1 for r in self.rows if r["result"] == result)

    def mean(self, key):
        return sum(r[key] for r in self.rows) / len(self.rows) if self.rows else 0.0

    def summary_lines(self):
        n = len(self.rows) or 1
        w, l, d = self.count("RUNNER_WIN"), self.count("GHOST_WIN"), self.count("DRAW")
        return [
            f"Matches played:      {len(self.rows)}",
            f"Runner AI wins:      {w}  ({100 * w / n:.0f}%)",
            f"Ghost AI wins:       {l}  ({100 * l / n:.0f}%)",
            f"Draws (time limit):  {d}  ({100 * d / n:.0f}%)",
            f"Average score:       {self.mean('score'):.0f}",
            f"Average level:       {self.mean('level'):.2f}",
            f"Minimax per move:    {self.mean('minimax_avg_nodes'):.0f} nodes, "
            f"{self.mean('minimax_avg_ms'):.2f} ms",
        ]

    def save_csv(self, path):
        if not self.rows:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)


def benchmark_search(maze, pairs=1000, seed=0):
    """Run A* and BFS on the SAME random start/goal pairs for a fair comparison."""
    rng = random.Random(seed)
    tiles = sorted(maze.runner_tiles)
    nbrs = maze.runner_nbrs.__getitem__
    result = {}
    jobs = [(rng.choice(tiles), rng.choice(tiles)) for _ in range(pairs)]
    for name, algo in (("A*", astar), ("BFS", bfs)):
        nodes, length = 0, 0
        start = time.perf_counter()
        for a, b in jobs:
            path, n = algo(a, b, nbrs)
            nodes += n
            length += max(len(path) - 1, 0)
        elapsed = time.perf_counter() - start
        result[name] = {"avg_nodes": nodes / pairs, "avg_ms": 1000 * elapsed / pairs,
                        "avg_path": length / pairs}
    return result