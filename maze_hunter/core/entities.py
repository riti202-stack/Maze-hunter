"""Moving things: the Runner and the ghosts.

Movement is tile based. A mover sits on `tile`, walks toward `target` and
`progress` goes from 0 to 1 along the way. Its drawn position is interpolated,
so motion looks smooth even though all decisions are made per tile.
"""
from maze_hunter.core.fsm import GhostFSM


class Mover:
    def __init__(self, tile):
        self.human = False
        self.reset(tile)

    def reset(self, tile):
        self.tile = tile
        self.target = tile
        self.progress = 0.0
        self.came_from = None       # previous tile (ghosts may not turn back onto it)
        self.facing = (0, 0)        # last direction of travel

    @property
    def moving(self):
        return self.target != self.tile

    @property
    def direction(self):
        if not self.moving:
            return (0, 0)
        return (self.target[0] - self.tile[0], self.target[1] - self.tile[1])

    @property
    def pos(self):
        """Position in tile units (floats), used for drawing and collisions."""
        x = self.tile[0] + (self.target[0] - self.tile[0]) * self.progress
        y = self.tile[1] + (self.target[1] - self.tile[1]) * self.progress
        return x, y

    def reverse(self):
        """Turn around immediately."""
        if self.moving:
            self.tile, self.target = self.target, self.tile
            self.progress = 1.0 - self.progress
            self.facing = self.direction
        self.came_from = None


class Runner(Mover):
    pass


class Ghost(Mover):
    def __init__(self, name, tile, color):
        self.name = name            # "A" (A* search) or "B" (BFS)
        self.color = color
        super().__init__(tile)

    def reset(self, tile):
        super().reset(tile)
        self.fsm = GhostFSM()
        self.release = 0.0          # seconds left before leaving the house
        self.path = []              # last planned path (shown in path view)
        self.goal = None            # last target tile (shown in path view)