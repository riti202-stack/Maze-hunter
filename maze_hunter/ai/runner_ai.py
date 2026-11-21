"""Agent 1 - Runner AI: depth-limited Minimax with alpha-beta pruning.

The Runner is the MAX player and every active ghost is a MIN player. One
"round" = the Runner moves one tile, then each ghost moves one tile. The search
looks `depth` rounds ahead (set by the difficulty) and scores the position at
the end with an evaluation function:

  + points for pellets eaten along the way (earlier = worth more)
  - distance to the nearest remaining pellet (a pellet is worth more than any
    distance, so the Runner never refuses food just to stay near more food)
  - danger from nearby ghosts (very large when a ghost is 0-2 tiles away)
  + bonus for being close to a frightened ghost it can catch
  Being caught = huge loss; eating the last pellet = huge win.

Alpha-beta pruning skips branches that cannot change the final decision, which
is what lets the search run inside a single frame.
"""
import time

from maze_hunter.core.fsm import EATEN, FRIGHTENED

INF = float("inf")
LOSS = -1_000_000.0
WIN = 1_000_000.0

# Evaluation weights. A pellet is worth more than the longest walk in the maze,
# so eating one always beats leaving it for later (avoids the horizon effect).
PELLET_VALUE = 100.0
POWER_VALUE = 1200.0         # only this high when a ghost is chasing nearby
CATCH_VALUE = 1000.0
FOOD_DISTANCE_WEIGHT = 1.0
DANGER_CLOSE = 9000.0        # ghost 0-2 tiles away
DANGER_NEAR = 500.0          # ghost 3-7 tiles away
PREY_PULL = 300.0


class RunnerAI:
    def __init__(self, maze, depth, rng, stats):
        self.maze = maze
        self.depth = depth
        self.rng = rng
        self.stats = stats
        self.last_choice = None     # shown in path view
        self.last_values = {}       # Minimax value of each move at the root

    # ---------------------------------------------------------------- entry point
    def choose(self, game):
        maze, runner = self.maze, game.runner
        moves = maze.runner_nbrs[runner.tile]
        if not moves:
            return None

        threats, preys = [], []
        for g in game.ghosts:
            state = g.fsm.state
            if state == EATEN:
                continue
            if g.moving and g.progress >= 0.5:
                tile, came_from = g.target, g.tile
            else:
                tile, came_from = g.tile, g.came_from
            # a ghost about to stop being frightened is treated as dangerous again
            if state == FRIGHTENED and g.fsm.fright_left > 1.5:
                preys.append(tile)
            else:
                threats.append((tile, came_from))

        self.pellets, self.power = game.pellets, game.power
        self.remaining = list(game.pellets | game.power)
        self.total = len(self.remaining)
        self.nodes = 0
        start = time.perf_counter()

        threats, preys = tuple(threats), tuple(preys)
        values = {}
        best = -INF
        # search the reverse move last so pruning helps most
        for m in sorted(moves, key=lambda t: t == runner.came_from):
            v = self._runner_step(m, threats, preys, frozenset(), 0.0,
                                  self.depth, 0, best - 1e-3, INF)
            values[m] = v
            best = max(best, v)

        candidates = [m for m, v in values.items() if v >= best - 1e-6]
        choice = self._tie_break(candidates, runner)
        self.stats.record("Minimax", self.nodes, time.perf_counter() - start)
        self.last_choice, self.last_values = choice, values
        return choice

    def _tie_break(self, candidates, runner):
        """Equal values: keep going straight, else avoid reversing, else random."""
        straight = (runner.tile[0] + runner.facing[0], runner.tile[1] + runner.facing[1])
        if straight in candidates:
            return straight
        forward = [m for m in candidates if m != runner.came_from]
        return self.rng.choice(forward or candidates)

    # ---------------------------------------------------------------- MAX (runner)
    def _runner_ply(self, r, threats, preys, eaten, gained, depth, ply, alpha, beta):
        best = -INF
        for m in self.maze.runner_nbrs[r]:
            v = self._runner_step(m, threats, preys, eaten, gained, depth, ply, alpha, beta)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break                                   # beta cut-off
        return best

    def _runner_step(self, m, threats, preys, eaten, gained, depth, ply, alpha, beta):
        """Apply the Runner's move to tile m, then let the ghosts reply."""
        self.nodes += 1
        ply += 1
        for gt, _ in threats:
            if gt == m:
                return LOSS + ply * 1000                # walked into a ghost
        weight = 1.0 + 0.2 * depth                      # earlier rewards count more
        if m not in eaten:
            if m in self.pellets:
                gained += PELLET_VALUE * weight
                eaten = eaten | {m}
            elif m in self.power:
                gdist = self.maze.ghost_dist
                danger = min((gdist[gt].get(m, 99) for gt, _ in threats), default=99)
                gained += (POWER_VALUE if danger <= 6 else PELLET_VALUE) * weight
                eaten = eaten | {m}
                preys = preys + tuple(gt for gt, _ in threats)   # ghosts turn blue
                threats = ()
        if m in preys:
            gained += CATCH_VALUE * weight
            preys = tuple(p for p in preys if p != m)
        if len(eaten) == self.total:
            return WIN - ply * 1000 + gained
        return self._ghost_ply(m, threats, preys, eaten, gained, depth, ply, 0, alpha, beta)

    # ---------------------------------------------------------------- MIN (ghosts)
    def _ghost_ply(self, r, threats, preys, eaten, gained, depth, ply, i, alpha, beta):
        if i == len(threats):                           # every ghost has moved
            if depth <= 1:
                return self.evaluate(r, threats, preys, eaten, gained)
            return self._runner_ply(r, threats, preys, eaten, gained, depth - 1, ply, alpha, beta)

        gt, came_from = threats[i]
        moves = self.maze.ghost_moves(gt)
        options = [n for n in moves if n != came_from] or list(moves)
        best = INF
        for n in options:
            self.nodes += 1
            if n == r:
                v = LOSS + (ply + 1) * 1000             # ghost catches the Runner
            else:
                moved = threats[:i] + ((n, gt),) + threats[i + 1:]
                v = self._ghost_ply(r, moved, preys, eaten, gained, depth, ply + 1, i + 1, alpha, beta)
            if v < best:
                best = v
            if best < beta:
                beta = best
            if alpha >= beta:
                break                                   # alpha cut-off
        return best

    # ---------------------------------------------------------------- evaluation
    def evaluate(self, r, threats, preys, eaten, gained):
        value = gained
        rdist = self.maze.runner_dist[r]
        nearest = None
        for p in self.remaining:
            if p not in eaten:
                d = rdist.get(p)
                if d is not None and (nearest is None or d < nearest):
                    nearest = d
        if nearest is not None:
            value -= FOOD_DISTANCE_WEIGHT * nearest

        gdist = self.maze.ghost_dist
        for gt, _ in threats:
            d = gdist[gt].get(r, 99)
            if d <= 2:
                value -= DANGER_CLOSE / (d + 1)
            elif d <= 7:
                value -= DANGER_NEAR / d
        for p in preys:
            value += PREY_PULL / (gdist[p].get(r, 99) + 1)
        return value