# src/agent.py
import os
import json
import random
import tempfile
from collections import defaultdict
from .config import ALPHA, GAMMA, EPS_START, EPS_END, EPS_DECAY, QTABLE_PATH

# ---------- state encoding ----------

def encode_state(obs, idx, env):
    """
    Compact local state around a candidate cell.
    State = (covered_neighbors, numbered_neighbors) bucketed to 0..3
    """
    opened = obs["opened"]
    adj = obs["adj"]
    neigh = env.neighbors(idx)

    covered = sum(1 for n in neigh if not opened[n])
    numbered = sum(1 for n in neigh if opened[n] and adj[n] > 0)

    def b(x):
        if x == 0: return 0
        if x == 1: return 1
        if x == 2: return 2
        return 3

    return str((b(covered), b(numbered)))


def sa_key(state, action):
    return f"{state}|{action}"


class QAgent:
    """
    Tabular Q-learning agent.
    """

    def __init__(self, env, qpath=QTABLE_PATH,
                 alpha=ALPHA, gamma=GAMMA):
        self.env = env

        self.qpath = qpath
        self.alpha = alpha
        self.gamma = gamma

        self.eps = EPS_START
        self.eps_end = EPS_END
        self.eps_decay = EPS_DECAY

        self.q = defaultdict(float)

        # load q-table if exists
        if os.path.exists(self.qpath):
            try:
                with open(self.qpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in data.items():
                    self.q[k] = float(v)
                print(f"[agent] loaded {len(self.q)} Q entries")
            except Exception as e:
                print("[agent] failed to load qtable:", e)

    # ---------- persistence ----------

    def _atomic_write(self, data):
        os.makedirs(os.path.dirname(self.qpath), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.qpath))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.qpath)

    def save(self):
        self._atomic_write(dict(self.q))
        print(f"[agent] saved {len(self.q)} Q entries")

    # ---------- action selection ----------

    def select(self, obs, legal, greedy=False):
        if not greedy and random.random() < self.eps:
            return random.choice(legal)

        best, bestv = None, -1e9
        for a in legal:
            s = encode_state(obs, a, self.env)
            v = self.q.get(sa_key(s, a), 0.0)
            if v > bestv:
                bestv, best = v, a

        return best if best is not None else random.choice(legal)

    # ---------- learning ----------

    def update(self, obs, action, reward, next_obs, done):
        s = encode_state(obs, action, self.env)
        k = sa_key(s, action)
        cur = self.q[k]

        if done:
            target = reward
        else:
            next_legal = [
                i for i in range(self.env.n)
                if not next_obs["opened"][i] and not next_obs["avoid"][i]
            ]
            if not next_legal:
                target = reward
            else:
                max_next = max(
                    self.q.get(
                        sa_key(encode_state(next_obs, a2, self.env), a2),
                        0.0
                    )
                    for a2 in next_legal
                )
                target = reward + self.gamma * max_next

        self.q[k] = cur + self.alpha * (target - cur)

        # epsilon decay
        self.eps = max(self.eps_end, self.eps * self.eps_decay)
