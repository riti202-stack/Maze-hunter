"""Game-wide constants and tuning values for Maze Hunter."""

# ---------------------------------------------------------------- display
TILE = 28                 # pixel size of one maze tile
HUD_HEIGHT = 64           # pixel height of the score bar above the maze
FPS = 60                  # target frames per second
DT = 1.0 / FPS            # fixed simulation step (seconds)

# ---------------------------------------------------------------- colours
BG = (11, 13, 30)
WALL_FILL = (26, 35, 126)
WALL_EDGE = (79, 107, 255)
DOOR = (255, 122, 198)
PELLET = (246, 231, 176)
POWER = (245, 200, 66)
RUNNER_COLOR = (245, 200, 66)
GHOST_A_COLOR = (255, 90, 95)      # red ghost, A* search
GHOST_B_COLOR = (255, 122, 198)    # pink ghost, BFS
FRIGHT_COLOR = (60, 90, 255)
FRIGHT_FLASH = (240, 240, 255)
EYE_WHITE = (246, 242, 231)
EYE_PUPIL = (26, 35, 126)
TEXT = (246, 242, 231)
MUTED = (185, 190, 218)
ACCENT = (245, 200, 66)
PANEL = (16, 18, 43)

# ---------------------------------------------------------------- speeds (tiles per second)
RUNNER_SPEED = 6.0
GHOST_BASE_SPEED = 5.4
LEVEL_SPEED_STEP = 0.35   # ghosts get this much faster each level
FRIGHT_SPEED = 3.2
EATEN_SPEED = 11.0

# ---------------------------------------------------------------- timing (seconds)
HOUSE_RELEASE = {"A": 0.0, "B": 3.0}   # how long each ghost waits before leaving home
FRIGHT_TIME = 6.0
FRIGHT_STEP = 1.5         # frightened time shrinks this much per level
FRIGHT_MIN = 2.0
READY_TIME = 1.5          # pause before play starts / after losing a life
MATCH_TIME_LIMIT = 300.0  # AI vs AI only: a match longer than this is a draw

# ---------------------------------------------------------------- rules
LIVES = 3
MAX_LEVEL = 3             # clearing this level wins the game
CATCH_RADIUS = 0.7        # tiles; closer than this counts as a catch

SCORE_PELLET = 10
SCORE_POWER = 50
SCORE_GHOST = (200, 400)  # first and second ghost caught per power pellet
SCORE_LEVEL = 500

# ---------------------------------------------------------------- difficulty
# ghost_speed: multiplier on ghost speed
# scatter / chase: length of each global FSM phase
# depth: Runner AI Minimax look-ahead, in full rounds (runner move + every ghost move)
DIFFICULTY = {
    "Easy":   {"ghost_speed": 0.85, "scatter": 7.0, "chase": 15.0, "depth": 2},
    "Medium": {"ghost_speed": 1.00, "scatter": 5.0, "chase": 20.0, "depth": 3},
    "Hard":   {"ghost_speed": 1.06, "scatter": 3.0, "chase": 25.0, "depth": 4},
}
DIFFICULTY_NAMES = ["Easy", "Medium", "Hard"]

# ---------------------------------------------------------------- modes
MODE_HUMAN_RUNNER = "Human vs AI"      # human = Runner, AI = ghosts
MODE_HUMAN_GHOST = "Human as Ghost"    # human = red ghost, AI = Runner + pink ghost
MODE_AI_VS_AI = "AI vs AI"             # Runner AI vs Ghost AI
MODES = [MODE_HUMAN_RUNNER, MODE_HUMAN_GHOST, MODE_AI_VS_AI]
MODE_INFO = {
    MODE_HUMAN_RUNNER: "You are the Runner. Eat every pellet and escape the Ghost AI.",
    MODE_HUMAN_GHOST: "You are the red ghost. Team up with the pink AI ghost to catch the Runner AI.",
    MODE_AI_VS_AI: "Runner AI vs Ghost AI. Watch, speed up with F, and compare results.",
}

HIGHSCORE_FILE = "highscore.json"