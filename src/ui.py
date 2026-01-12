# src/ui.py
import pygame, os, time, random
from pathlib import Path
from .config import *
from .env import MinesweeperEnv
from .agent import QAgent
from .utils import load_image, generate_placeholder_assets

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
NUM_DIR = os.path.join(ASSET_DIR, "numbers")


class MinesweeperUI:
    def __init__(self):
        pygame.init()
        self.cell = CELL_PIX

        # screen with HUD space
        self.screen = pygame.display.set_mode(
            (COLS * self.cell + MARGIN * 2,
             ROWS * self.cell + MARGIN * 2 + 110)
        )
        pygame.display.set_caption("Minesweeper Q-Learning (8×8)")
        self.clock = pygame.time.Clock()

        # ---------- assets ----------
        Path(ASSET_DIR).mkdir(parents=True, exist_ok=True)
        if not os.path.exists(os.path.join(ASSET_DIR, "tile.png")):
            generate_placeholder_assets(ASSET_DIR, self.cell)

        self.img_tile = load_image(os.path.join(ASSET_DIR, "tile.png"), (self.cell, self.cell))
        self.img_open = load_image(os.path.join(ASSET_DIR, "tile_open.png"), (self.cell, self.cell))
        self.img_bomb = load_image(os.path.join(ASSET_DIR, "bomb.png"), (self.cell, self.cell))

        self.img_nums = {}
        for i in range(1, 9):
            p = os.path.join(NUM_DIR, f"{i}.png")
            if os.path.exists(p):
                self.img_nums[i] = load_image(p, (self.cell, self.cell))

        self.font = pygame.font.SysFont("Arial", 18)
        self.bigfont = pygame.font.SysFont("Arial", 32, bold=True)

        # ---------- env + agent ----------
        self.env = MinesweeperEnv(rows=ROWS, cols=COLS, mines=MINES)
        self.agent = QAgent(self.env)

        # ---------- modes ----------
        self.auto = True        # A → toggle AUTO / MANUAL
        self.train = True       # SPACE → toggle learning
        self.greedy = False     # G → greedy policy (evaluation)

        # ---------- episode state ----------
        self.episode_reward = 0.0
        self.last_selected = None

        # ---------- end visuals ----------
        self.end_state = None               # "win" or "loss"
        self.show_end_until = 0.0
        self.win_pause = 2.2
        self.loss_pause = 1.6

        # ---------- stats ----------
        self.win_count = 0
        self.loss_count = 0

        # ---------- confetti ----------
        self.particles = []

    # =========================================================
    # 🎉 CONFETTI (WIN)
    # =========================================================
    def spawn_confetti(self, n=60):
        for _ in range(n):
            self.particles.append({
                "x": random.uniform(MARGIN, MARGIN + COLS * self.cell),
                "y": random.uniform(MARGIN - 30, MARGIN + ROWS * self.cell * 0.3),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(1.0, 3.0),
                "size": random.randint(3, 6),
                "color": random.choice([
                    (255, 200, 60), (255, 120, 140),
                    (120, 220, 120), (120, 160, 255)
                ]),
                "life": time.time() + random.uniform(1.0, 2.0)
            })

    def update_particles(self):
        now = time.time()
        self.particles = [p for p in self.particles if p["life"] > now]
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.08

    # =========================================================
    # 🎨 DRAW
    # =========================================================
    def draw(self):
        self.screen.fill((32, 32, 32))
        obs = self.env.observe()

        # ---------- board ----------
        for r in range(ROWS):
            for c in range(COLS):
                i = self.env.rc_to_i(r, c)
                x = MARGIN + c * self.cell
                y = MARGIN + r * self.cell
                rect = pygame.Rect(x, y, self.cell, self.cell)

                if obs["opened"][i]:
                    self.screen.blit(self.img_open, (x, y))
                    if obs["adj"][i] > 0:
                        img = self.img_nums.get(obs["adj"][i])
                        if img:
                            self.screen.blit(img, (x, y))
                else:
                    self.screen.blit(self.img_tile, (x, y))

                if self.last_selected == i:
                    pygame.draw.rect(self.screen, (220, 60, 60), rect, 3)

        # ---------- overlays (WIN / BOOM) ----------
        now = time.time()
        if self.show_end_until > now:
            overlay = pygame.Surface((COLS * self.cell, ROWS * self.cell), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            self.screen.blit(overlay, (MARGIN, MARGIN))

            if self.end_state == "loss":
                for i in range(self.env.n):
                    if self.env.mine[i]:
                        r, c = self.env.i_to_rc(i)
                        self.screen.blit(
                            self.img_bomb,
                            (MARGIN + c * self.cell, MARGIN + r * self.cell)
                        )
                msg = "BOOOOM! :("
                col = (255, 120, 120)
            else:
                self.update_particles()
                for p in self.particles:
                    pygame.draw.rect(
                        self.screen, p["color"],
                        pygame.Rect(p["x"], p["y"], p["size"], p["size"])
                    )
                msg = "YAY! YOU WIN!"
                col = (200, 255, 200)

            text = self.bigfont.render(msg, True, col)
            self.screen.blit(
                text,
                ((self.screen.get_width() - text.get_width()) // 2, 10)
            )

        # ---------- HUD ----------
        hud_y = MARGIN + ROWS * self.cell + 8
        hud = pygame.Surface((self.screen.get_width(), 60), pygame.SRCALPHA)
        hud.fill((15, 15, 15, 230))
        self.screen.blit(hud, (0, hud_y))

        # left HUD (modes)
        left = (
            f"A = {'AUTO' if self.auto else 'MANUAL'}   | "
            f"SPACE = {'TRAIN' if self.train else 'EVAL'}   | "
            f"G = {'GREEDY' if self.greedy else 'EPS-GREEDY'}"
        )
        self.screen.blit(self.font.render(left, True, (230, 230, 230)), (MARGIN, hud_y + 6))

        # right HUD (stats)
        right = f"Wins: {self.win_count}   Losses: {self.loss_count}"
        txt = self.font.render(right, True, (230, 230, 230))
        self.screen.blit(txt, (self.screen.get_width() - txt.get_width() - 20, hud_y + 6))

        pygame.display.flip()

    # =========================================================
    # 🤖 AGENT STEP (AUTO MODE)
    # =========================================================
    def step_agent(self):
        obs = self.env.observe()
        legal = self.env.legal_actions()
        if not legal:
            return

        action = self.agent.select(obs, legal, greedy=self.greedy)
        self.last_selected = action

        reward, done, _ = self.env.open_cell(action)
        self.episode_reward += reward

        if self.train:
            self.agent.update(obs, action, reward, self.env.observe(), done)

        if done:
            self.agent.save()
            if self.env.win:
                self.win_count += 1
                self.end_state = "win"
                self.spawn_confetti()
                self.show_end_until = time.time() + self.win_pause
            else:
                self.loss_count += 1
                self.end_state = "loss"
                self.show_end_until = time.time() + self.loss_pause

    # =========================================================
    # 🎮 MAIN LOOP
    # =========================================================
    def run(self):
        running = True
        tick = 0

        while running:
            now = time.time()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_a:       # A = AUTO / MANUAL
                        self.auto = not self.auto
                    elif ev.key == pygame.K_SPACE: # SPACE = TRAIN / EVAL
                        self.train = not self.train
                    elif ev.key == pygame.K_g:     # G = GREEDY
                        self.greedy = not self.greedy

                # MANUAL PLAY (mouse click)
                elif ev.type == pygame.MOUSEBUTTONDOWN and not self.auto:
                    mx, my = pygame.mouse.get_pos()
                    if my < MARGIN + ROWS * self.cell:
                        c = (mx - MARGIN) // self.cell
                        r = (my - MARGIN) // self.cell
                        if 0 <= r < ROWS and 0 <= c < COLS:
                            idx = self.env.rc_to_i(r, c)
                            reward, done, _ = self.env.open_cell(idx)
                            self.episode_reward += reward
                            if done:
                                if self.env.win:
                                    self.win_count += 1
                                    self.end_state = "win"
                                    self.spawn_confetti()
                                    self.show_end_until = time.time() + self.win_pause
                                else:
                                    self.loss_count += 1
                                    self.end_state = "loss"
                                    self.show_end_until = time.time() + self.loss_pause

            # pause screen on win/loss
            if self.show_end_until > now:
                self.draw()
                self.clock.tick(30)
                continue
            elif self.show_end_until and self.show_end_until <= now:
                self.show_end_until = 0
                self.particles.clear()
                self.last_selected = None
                self.env.reset()
                self.episode_reward = 0.0

            # AUTO mode
            if self.auto:
                if tick % 6 == 0:
                    self.step_agent()
                tick += 1

            self.draw()
            self.clock.tick(30)

        pygame.quit()
