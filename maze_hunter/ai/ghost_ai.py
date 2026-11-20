"""Agent 2 - Ghost AI. Controls every ghost that is not driven by a human.

Ghost A (red):  A* search to the Runner's current tile  -> direct chase
Ghost B (pink): BFS to the tile 4 steps ahead of the Runner -> cuts it off
Both obey the FSM in fsm.py (Scatter / Chase / Frightened / Eaten).
"""
import time

from maze_hunter.core.fsm import EATEN, FRIGHTENED, SCATTER
from maze_hunter.core.maze import add
from maze_hunter.ai.search import astar, bfs

AMBUSH_STEPS = 4


class GhostAI:
    def __init__(self, maze, rng, stats):
        self.maze = maze
        self.rng = rng
        self.stats = stats

    def ahead_of_runner(self, runner):
        """Ghost B's target: up to 4 open tiles in front of the Runner."""
        d = runner.direction if runner.moving else runner.facing
        tile = runner.tile
        if d == (0, 0):
            return tile
        for _ in range(AMBUSH_STEPS):
            nxt = add(tile, d)
            if nxt not in self.maze.runner_tiles:
                break
            tile = nxt
        return tile

    def target_for(self, ghost, game):
        if ghost.fsm.state == SCATTER:
            return self.maze.corners[ghost.name]
        if ghost.name == "A":
            return game.runner.tile
        goal = self.ahead_of_runner(game.runner)
        return game.runner.tile if goal == ghost.tile else goal

    def _random_move(self, ghost):
        moves = list(self.maze.ghost_moves(ghost.tile))
        options = [m for m in moves if m != ghost.came_from] or moves
        return self.rng.choice(options) if options else None

    def choose(self, ghost, game):
        """Return the next tile this ghost should walk to."""
        maze = self.maze
        state = ghost.fsm.state

        if state == EATEN:                                   # eyes go home by BFS
            path, _ = bfs(ghost.tile, maze.home, maze.ghost_nbrs.__getitem__)
            ghost.path, ghost.goal = path, maze.home
            return path[1] if len(path) > 1 else None

        if state == FRIGHTENED:                              # random, no searching
            ghost.path, ghost.goal = [], None
            return self._random_move(ghost)

        goal = self.target_for(ghost, game)
        algo, name = (astar, "A*") if ghost.name == "A" else (bfs, "BFS")
        start = time.perf_counter()
        path, nodes = algo(ghost.tile, goal, maze.ghost_moves, ghost.came_from)
        self.stats.record(name, nodes, time.perf_counter() - start)
        ghost.path, ghost.goal = path, goal
        if len(path) > 1:
            return path[1]
        return self._random_move(ghost)                     # already on the goal tile