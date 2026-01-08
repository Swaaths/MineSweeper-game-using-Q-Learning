# src/config.py
import os

# ==============================
# Board configuration
# ==============================
ROWS = 10
COLS = 10
MINES = 3

CELL_PIX = 64
MARGIN = 12


# ==============================
# Q-learning hyperparameters
# ==============================
ALPHA = 0.3          # learning rate
GAMMA = 0.95         # discount factor

# exploration
EPS_START = 0.6
EPS_END = 0.02
EPS_DECAY = 0.9992


# ==============================
# Reward shaping
# ==============================
REWARD_SAFE = 0.12        # opening a non-mine cell
REWARD_ZERO = 0.25       # flood-fill (zero-adjacent)
REWARD_WIN = 4.0         # winning the game

PENALTY_MINE = -2.0      # stepping on a mine
STEP_PENALTY = -0.002    # small penalty per step (encourages efficiency)


# ==============================
# Paths (robust + absolute)
# ==============================
# Project root = parent of src/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

QTABLE_PATH = os.path.join(MODELS_DIR, "qtable.json")
