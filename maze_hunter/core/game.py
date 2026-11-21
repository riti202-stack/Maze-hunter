"""Core game rules: movement, pellets, lives, levels and the three modes.

This file has no pygame code, so the same rules run in the window and in the
headless AI vs AI evaluation.
"""
import math
import random

from maze_hunter.core.entities import Ghost, Runner
from maze_hunter.core.fsm import EATEN, FRIGHTENED, ModeSchedule
from maze_hunter.ai.ghost_ai import GhostAI
from maze_hunter.core.maze import Maze, add
from maze_hunter.ai.runner_ai import RunnerAI
from maze_hunter.ai.search import bfs
from maze_hunter.config.settings import (CATCH_RADIUS, DIFFICULTY, EATEN_SPEED, FRIGHT_MIN, FRIGHT_SPEED,
                      FRIGHT_STEP, FRIGHT_TIME, GHOST_A_COLOR, GHOST_B_COLOR,
                      GHOST_BASE_SPEED, HOUSE_RELEASE, LEVEL_SPEED_STEP, LIVES,
                      MATCH_TIME_LIMIT, MAX_LEVEL, MODE_AI_VS_AI, MODE_HUMAN_GHOST,
                      MODE_HUMAN_RUNNER, READY_TIME, RUNNER_SPEED, SCORE_GHOST,
                      SCORE_LEVEL, SCORE_PELLET, SCORE_POWER)
from maze_hunter.analysis.stats import SearchStats

RUNNER_WIN = "RUNNER_WIN"
GHOST_WIN = "GHOST_WIN"
DRAW = "DRAW"


class Game:
    def __init__(self, mode, difficulty="Medium", seed=None, maze=None):
        self.mode = mode
        self.difficulty = difficulty
        self.cfg = DIFFICULTY[difficulty]
        self.maze = maze or Maze()
        self.rng = random.Random(seed)
        self.stats = SearchStats()
        self.time_limit = MATCH_TIME_LIMIT if mode == MODE_AI_VS_AI else None

        m = self.maze
        self.runner = Runner(m.runner_start)
        self.ghosts = [Ghost("A", m.ghost_starts["A"], GHOST_A_COLOR),
                       Ghost("B", m.ghost_starts["B"], GHOST_B_COLOR)]

        # who is controlled by the keyboard?
        self.runner.human = mode == MODE_HUMAN_RUNNER
        self.ghosts[0].human = mode == MODE_HUMAN_GHOST
        self.human_entity = (self.runner if self.runner.human
                             else self.ghosts[0] if self.ghosts[0].human else None)

        self.runner_ai = None if self.runner.human else RunnerAI(m, self.cfg["depth"], self.rng, self.stats)
        self.ghost_ai = GhostAI(m, self.rng, self.stats)

        self.score = 0
        self.lives = LIVES
        self.level = 1
        self.elapsed = 0.0
        self.result = None
        self.human_dir = None
        self._start_level()

    # ---------------------------------------------------------------- setup
    def _start_level(self):
        self.pellets = set(self.maze.pellet_start)
        self.power = set(self.maze.power_start)
        self.schedule = ModeSchedule(self.cfg["scatter"], self.cfg["chase"])
        self._reset_positions()

    def _reset_positions(self):
        self.runner.reset(self.maze.runner_start)
        for g in self.ghosts:
            g.reset(self.maze.ghost_starts[g.name])
            g.release = HOUSE_RELEASE[g.name]
        self.ready = READY_TIME
        self.combo = 0
        self.human_dir = None

    # ---------------------------------------------------------------- tuning helpers
    def ghost_speed(self, ghost):
        if ghost.fsm.state == EATEN:
            return EATEN_SPEED
        if ghost.fsm.state == FRIGHTENED:
            return FRIGHT_SPEED
        return (GHOST_BASE_SPEED + LEVEL_SPEED_STEP * (self.level - 1)) * self.cfg["ghost_speed"]

    def fright_duration(self):
        return max(FRIGHT_MIN, FRIGHT_TIME - FRIGHT_STEP * (self.level - 1))

    @property
    def time_left(self):
        return None if self.time_limit is None else max(0.0, self.time_limit - self.elapsed)

    # ---------------------------------------------------------------- input
    def set_human_direction(self, d):
        """Called by the window when an arrow key is pressed."""
        self.human_dir = d
        e = self.human_entity
        if e is None or (isinstance(e, Ghost) and e.fsm.state == EATEN):
            return
        if e.moving and e.direction == (-d[0], -d[1]):
            e.reverse()                                  # instant U-turn feels responsive

    def _human_choice(self, entity, allowed):
        """Buffered steering: take the wanted turn as soon as it is open."""
        if self.human_dir:
            nxt = add(entity.tile, self.human_dir)
            if nxt in allowed:
                return nxt
        if entity.facing != (0, 0):
            nxt = add(entity.tile, entity.facing)
            if nxt in allowed:
                return nxt
        return None                                      # stop at the wall

    # ---------------------------------------------------------------- main update
    def update(self, dt):
        if self.result:
            return
        self.elapsed += dt
        if self.time_limit is not None and self.elapsed >= self.time_limit:
            self.result = DRAW
            return
        if self.ready > 0:
            self.ready -= dt
            return

        self.schedule.update(dt)
        for g in self.ghosts:
            if g.fsm.update(dt, self.schedule.mode) and not g.human:
                g.reverse()                              # classic: reverse on mode change

        self._move(self.runner, RUNNER_SPEED, dt, self._runner_choice, self._runner_arrived)
        if self.result or self.ready > 0:
            return
        self._check_collisions()
        if self.result or self.ready > 0:
            return
        for g in self.ghosts:
            if g.release > 0:
                g.release -= dt
                continue
            self._move(g, self.ghost_speed(g), dt, self._ghost_choice, self._ghost_arrived)
        self._check_collisions()

    def _move(self, ent, speed, dt, choose, arrived):
        remaining = speed * dt
        for _ in range(3):
            if remaining <= 1e-9:
                break
            if not ent.moving:
                nxt = choose(ent)
                if nxt is None or nxt == ent.tile:
                    break
                ent.target = nxt
                ent.progress = 0.0
                ent.facing = ent.direction
            step = min(remaining, 1.0 - ent.progress)
            ent.progress += step
            remaining -= step
            if ent.progress >= 1.0 - 1e-9:
                ent.came_from, ent.tile, ent.progress = ent.tile, ent.target, 0.0
                arrived(ent)
                if self.result or self.ready > 0:
                    break

    # ---------------------------------------------------------------- decisions
    def _runner_choice(self, runner):
        if runner.human:
            return self._human_choice(runner, self.maze.runner_nbrs[runner.tile])
        return self.runner_ai.choose(self)

    def _ghost_choice(self, ghost):
        if ghost.human and ghost.fsm.state != EATEN:
            return self._human_choice(ghost, self.maze.ghost_moves(ghost.tile))
        return self.ghost_ai.choose(ghost, self)        # eaten human ghost goes home by AI# eaten human ghost goes home by AI

    # ---------------------------------------------------------------- events
    def _runner_arrived(self, runner):
        t = runner.tile
        if t in self.pellets:
            self.pellets.discard(t)
            self.score += SCORE_PELLET
        elif t in self.power:
            self.power.discard(t)
            self.score += SCORE_POWER
            self.combo = 0
            duration = self.fright_duration()
            for g in self.ghosts:
                if g.fsm.frighten(duration) and not g.human:
                    g.reverse()
        if not self.pellets and not self.power:
            self._level_cleared()

    def _ghost_arrived(self, ghost):
        if ghost.fsm.state == EATEN and ghost.tile == self.maze.home:
            ghost.fsm.reached_home(self.schedule.mode)
            ghost.came_from = None

    def _check_collisions(self):
        rx, ry = self.runner.pos
        for g in self.ghosts:
            gx, gy = g.pos
            if math.hypot(rx - gx, ry - gy) >= CATCH_RADIUS:
                continue
            if g.fsm.state == FRIGHTENED:
                self.score += SCORE_GHOST[min(self.combo, len(SCORE_GHOST) - 1)]
                self.combo += 1
                g.fsm.caught()
            elif g.fsm.state != EATEN:
                self._runner_caught()
                return

    def _runner_caught(self):
        self.lives -= 1
        if self.lives <= 0:
            self.result = GHOST_WIN
        else:
            self._reset_positions()                      # pellets already eaten stay eaten

    def _level_cleared(self):
        self.score += SCORE_LEVEL
        if self.level >= MAX_LEVEL:
            self.result = RUNNER_WIN
        else:
            self.level += 1
            self._start_level()


def result_text(game):
    """Headline and sub-line for the end screen, from the human's point of view."""
    if game.mode == MODE_HUMAN_RUNNER:
        return {RUNNER_WIN: ("YOU WIN!", "You cleared every level."),
                GHOST_WIN: ("GAME OVER", "The Ghost AI caught you.")}[game.result]
    if game.mode == MODE_HUMAN_GHOST:
        return {GHOST_WIN: ("YOU WIN!", "You caught the Runner AI."),
                RUNNER_WIN: ("THE RUNNER ESCAPED", "The Runner AI cleared every level.")}[game.result]
    return {RUNNER_WIN: ("RUNNER AI WINS", "All levels cleared."),
            GHOST_WIN: ("GHOST AI WINS", "The Runner lost all lives."),
            DRAW: ("DRAW", "Time limit reached.")}[game.result]