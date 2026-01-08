# utils.py
import os
from pathlib import Path

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def load_image(path, scale=None):
    """
    Load an image with pygame, print debug info, and return a scaled surface if requested.
    """
    import pygame, os, traceback
    path = os.path.abspath(path)
    print(f"[load_image] loading: {path} (exists={os.path.exists(path)})")
    try:
        img = pygame.image.load(path)
        try:
            img = img.convert_alpha()
        except Exception as e:
            print("[load_image] convert_alpha failed:", e)
            img = img.convert()
        if scale:
            img = pygame.transform.smoothscale(img, scale)
        print(f"[load_image] loaded ok: size={img.get_size()}")
        return img
    except Exception as e:
        print("[load_image] ERROR loading image:", e)
        traceback.print_exc()
        raise

def generate_placeholder_assets(out_dir, cell_sz):
    """
    Create simple placeholder pngs if artist assets missing.
    Writes into out_dir/tile.png, tile_open.png, flag.png, bomb.png and numbers/1..8.png
    """
    try:
        import pygame
    except Exception as e:
        raise RuntimeError("pygame required to generate placeholder assets. Install pygame first.") from e

    ensure_dir(out_dir)
    numbers_dir = os.path.join(out_dir, "numbers")
    ensure_dir(numbers_dir)

    # Initialize pygame display temporarily to allow font rendering
    pygame.init()
    # closed tile
    surf = pygame.Surface((cell_sz, cell_sz), pygame.SRCALPHA)
    surf.fill((180,180,180))
    pygame.draw.rect(surf, (150,150,150), surf.get_rect(), 4, border_radius=6)
    pygame.image.save(surf, os.path.join(out_dir, "tile.png"))
    # opened tile
    surf2 = pygame.Surface((cell_sz, cell_sz), pygame.SRCALPHA)
    surf2.fill((245,245,245))
    pygame.draw.rect(surf2, (220,220,220), surf2.get_rect(), 4, border_radius=6)
    pygame.image.save(surf2, os.path.join(out_dir, "tile_open.png"))
    # flag
    surf_flag = pygame.Surface((cell_sz, cell_sz), pygame.SRCALPHA)
    pygame.draw.polygon(surf_flag, (200,60,60), [(10,8),(10,40),(38,24)])
    pygame.draw.line(surf_flag, (80,80,80), (12,6), (12,48), 3)
    pygame.image.save(surf_flag, os.path.join(out_dir, "flag.png"))
    # bomb
    surf_bomb = pygame.Surface((cell_sz, cell_sz), pygame.SRCALPHA)
    pygame.draw.circle(surf_bomb, (30,30,30),(cell_sz//2,cell_sz//2),cell_sz//4)
    pygame.image.save(surf_bomb, os.path.join(out_dir, "bomb.png"))
    # numbers
    try:
        font = pygame.font.SysFont("Arial", int(cell_sz*0.7), bold=True)
    except Exception:
        pygame.font.init()
        font = pygame.font.SysFont("Arial", int(cell_sz*0.7), bold=True)

    colors = [(0,0,0),(25,25,180),(20,120,20),(180,20,20),(60,60,160),(140,20,20),(20,140,140),(20,20,20),(100,100,100)]
    for i in range(1,9):
        s = pygame.Surface((cell_sz, cell_sz), pygame.SRCALPHA)
        txt = font.render(str(i), True, colors[i])
        tw, th = txt.get_size()
        s.blit(txt, ((cell_sz-tw)//2, (cell_sz-th)//2))
        pygame.image.save(s, os.path.join(numbers_dir, f"{i}.png"))

    pygame.quit()
    print("[utils] placeholder assets created in", out_dir)
