# run_train.py
import time
from src.env import MinesweeperEnv
from src.agent import QAgent
from src.config import ROWS, COLS, MINES


def train_loop(
    episodes=8000,        # 🔹 CHANGE THIS TO TRAIN MORE / LESS
    report_every=100,
    save_every=500
):
    """
    Headless Q-learning training loop.
    Trains without UI and saves qtable.json.
    """

    env = MinesweeperEnv(rows=ROWS, cols=COLS, mines=MINES)
    agent = QAgent(env)

    wins = 0
    recent_wins = []
    start_time = time.time()

    for ep in range(1, episodes + 1):
        obs = env.reset()
        done = False

        while not done:
            legal = env.legal_actions()
            if not legal:
                break

            action = agent.select(obs, legal, greedy=False)
            reward, done, _ = env.open_cell(action)
            next_obs = env.observe()

            agent.update(obs, action, reward, next_obs, done)
            obs = next_obs

        # record win
        win = 1 if env.win else 0
        wins += win
        recent_wins.append(win)
        if len(recent_wins) > 100:
            recent_wins.pop(0)

        # progress report
        if ep % report_every == 0:
            recent_rate = sum(recent_wins) / len(recent_wins)
            overall_rate = wins / ep
            elapsed = time.time() - start_time

            print(
                f"EP {ep:5d} | "
                f"recent win-rate={recent_rate:.2f} | "
                f"overall={overall_rate:.2f} | "
                f"eps={agent.eps:.3f} | "
                f"time={elapsed:.1f}s"
            )

        # save Q-table periodically
        if ep % save_every == 0:
            agent.save()

    # final save
    agent.save()
    print("\nTraining finished")
    print(f"Total episodes: {episodes}")
    print(f"Final win rate: {wins / episodes:.2f}")


if __name__ == "__main__":
    train_loop(
        episodes=8000,     # 🔹 CHANGE THIS NUMBER IF NEEDED
        report_every=100,
        save_every=500
    )
