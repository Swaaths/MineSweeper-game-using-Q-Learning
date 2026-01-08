# src/env.py
import random
from .config import (
    ROWS, COLS, MINES,
    REWARD_SAFE, REWARD_ZERO, REWARD_WIN,
    PENALTY_MINE, STEP_PENALTY
)

class MinesweeperEnv:
    """
    Minesweeper environment with:
    - first-click safety
    - flood fill
    - NO flags
    - deterministic inference
    - avoid-mask instead of flags
    """

    def __init__(self, rows=ROWS, cols=COLS, mines=MINES, seed=None):
        self.rows = rows
        self.cols = cols
        self.n = rows * cols
        self.mines = mines
        self.rng = random.Random(seed)
        self.reset()

    # ---------- core ----------

    def reset(self):
        self.mine = [0] * self.n
        self.opened = [0] * self.n
        self.adj = [0] * self.n

        # cells that logic marks unsafe
        self.avoid = [0] * self.n

        self.placed = False
        self.done = False
        self.win = False
        self.steps = 0
        return self.observe()

    # ---------- helpers ----------

    def rc_to_i(self, r, c):
        return r * self.cols + c

    def i_to_rc(self, i):
        return divmod(i, self.cols)

    def neighbors(self, i):
        r, c = self.i_to_rc(i)
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    out.append(self.rc_to_i(nr, nc))
        return out

    # ---------- mines ----------

    def place_mines(self, safe_i):
        forbidden = set(self.neighbors(safe_i) + [safe_i])
        candidates = [i for i in range(self.n) if i not in forbidden]
        self.rng.shuffle(candidates)

        for i in candidates[:self.mines]:
            self.mine[i] = 1

        for i in range(self.n):
            self.adj[i] = sum(self.mine[n] for n in self.neighbors(i))

        self.placed = True

    # ---------- observation ----------

    def observe(self):
        return {
            "opened": self.opened.copy(),
            "adj": self.adj.copy(),
            "avoid": self.avoid.copy(),
        }

    # ---------- actions ----------

    def legal_actions(self):
        return [
            i for i in range(self.n)
            if not self.opened[i] and not self.avoid[i]
        ]

    # ---------- gameplay ----------

    def open_cell(self, i):
        if self.done:
            return 0.0, True, {}

        if not self.placed:
            self.place_mines(i)

        if self.opened[i] or self.avoid[i]:
            return 0.0, False, {"illegal": True}

        self.steps += 1

        # mine
        if self.mine[i]:
            self.opened[i] = 1
            self.done = True
            self.win = False
            return PENALTY_MINE, True, {"mine": True}

        # safe
        reward = REWARD_SAFE + STEP_PENALTY

        if self.adj[i] == 0:
            self._flood(i)
            reward += REWARD_ZERO
        else:
            self.opened[i] = 1

        # win check
        safe_opened = sum(
            1 for j in range(self.n)
            if self.opened[j] and not self.mine[j]
        )
        if safe_opened == self.n - self.mines:
            self.done = True
            self.win = True
            reward += REWARD_WIN

        return reward, self.done, {}

    # ---------- flood ----------

    def _flood(self, start):
        q = [start]
        seen = {start}
        while q:
            cur = q.pop(0)
            self.opened[cur] = 1
            if self.adj[cur] == 0:
                for nb in self.neighbors(cur):
                    if nb not in seen and not self.opened[nb]:
                        seen.add(nb)
                        q.append(nb)

    # ---------- deterministic logic ----------

    def deterministic_inference_once(self):
        """
        Applies basic Minesweeper rules.
        Returns True if something changed.
        """
        changed = False

        for i in range(self.n):
            if not self.opened[i]:
                continue

            number = self.adj[i]
            if number <= 0:
                continue

            neigh = self.neighbors(i)
            covered = [n for n in neigh if not self.opened[n]]

            if not covered:
                continue

            # Rule 1: all covered are mines
            if number == len(covered):
                for n in covered:
                    if not self.avoid[n]:
                        self.avoid[n] = 1
                        changed = True

            # Rule 2: all mines accounted → rest safe
            avoided = sum(self.avoid[n] for n in neigh)
            if avoided == number:
                for n in covered:
                    if not self.avoid[n]:
                        self.open_cell(n)
                        changed = True

        return changed
