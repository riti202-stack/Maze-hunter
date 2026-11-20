"""Finite State Machine that controls each ghost's behaviour mode.

States
  Scatter    -> go to the ghost's home corner (gives the player breathing room)
  Chase      -> hunt the Runner
  Frightened -> after a power pellet: slow, random moves, can be caught
  Eaten      -> caught by the Runner: eyes rush back home, then rejoin the game

Transitions
  Scatter <-> Chase      global timer (ModeSchedule), every ghost reverses direction
  any (not Eaten) -> Frightened   Runner eats a power pellet
  Frightened -> Scatter/Chase     frightened timer runs out
  Frightened -> Eaten             Runner touches the ghost
  Eaten -> Scatter/Chase          ghost reaches home
"""

SCATTER = "Scatter"
CHASE = "Chase"
FRIGHTENED = "Frightened"
EATEN = "Eaten"


class ModeSchedule:
    """The global Scatter/Chase clock shared by all ghosts."""

    def __init__(self, scatter_time, chase_time):
        self.scatter_time = scatter_time
        self.chase_time = chase_time
        self.mode = SCATTER
        self.timer = scatter_time

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            if self.mode == SCATTER:
                self.mode, self.timer = CHASE, self.timer + self.chase_time
            else:
                self.mode, self.timer = SCATTER, self.timer + self.scatter_time


class GhostFSM:
    def __init__(self, start_state=SCATTER):
        self.state = start_state
        self.fright_left = 0.0

    def update(self, dt, global_mode):
        """Advance timers. Returns True when the ghost should reverse direction."""
        if self.state == FRIGHTENED:
            self.fright_left -= dt
            if self.fright_left <= 0:
                self.state = global_mode
            return False
        if self.state in (SCATTER, CHASE) and self.state != global_mode:
            self.state = global_mode
            return True
        return False

    def frighten(self, duration):
        """Power pellet eaten. Returns True if the ghost became frightened."""
        if self.state == EATEN:
            return False
        self.state = FRIGHTENED
        self.fright_left = duration
        return True

    def caught(self):
        self.state = EATEN
        self.fright_left = 0.0

    def reached_home(self, global_mode):
        self.state = global_mode