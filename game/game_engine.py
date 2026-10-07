import random
import pygame
from game.maze import generate_maze, build_wall_rects, CELL
from game.entities import Player, Enemy, PowerPellet

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60

# Task 2: difficulty ramp settings
RAMP_INTERVAL_MS = 15_000     # every 15 seconds...
RAMP_STEP = 2                 # ...enemy.move_interval drops by 2
MIN_MOVE_INTERVAL = 5         # ...but never below 5
START_MOVE_INTERVAL = 20

# Task 3: power pellet settings
FREEZE_FRAMES = 300           # 5 seconds at 60 FPS


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.hud_font = pygame.font.SysFont("monospace", 17, bold=True)
        self.exit_font = pygame.font.SysFont("monospace", 13, bold=True)
        self.hint_font = pygame.font.SysFont("monospace", 13)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.wall_rects = build_wall_rects(self.walls, ROWS, COLS)
        self.player = Player(0, 0)

        # Task 1: three independent enemies, one in each of the other corners.
        # Timers are staggered so they don't all step on the same frame.
        self.enemies = [
            Enemy(ROWS - 1, COLS - 1, timer_offset=0),
            Enemy(0, COLS - 1, timer_offset=7),
            Enemy(ROWS - 1, 0, timer_offset=14),
        ]

        self.exit_rect = pygame.Rect((COLS // 2) * CELL + 5, (ROWS // 2) * CELL + 5, CELL - 10, CELL - 10)

        # Task 3: place the pellet in a random cell that isn't a spawn point or the exit.
        blocked = {(0, 0), (ROWS - 1, COLS - 1), (0, COLS - 1), (ROWS - 1, 0), (ROWS // 2, COLS // 2)}
        cells = [(r, c) for r in range(ROWS) for c in range(COLS)
                 if (r, c) not in blocked and r + c >= 4]      # not right next to the player's start
        self.pellet = PowerPellet(*random.choice(cells))
        self.freeze_timer = 0

        # Task 2: speed ramp state
        self.start_ticks = pygame.time.get_ticks()
        self.speed_tier = 0
        self.move_interval = START_MOVE_INTERVAL

        # Task 4: survival score (frames survived)
        self.score = 0

        self.caught = False
        self.won = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    # ---- Task 2 ----
    def _update_difficulty(self):
        elapsed = pygame.time.get_ticks() - self.start_ticks
        tier = elapsed // RAMP_INTERVAL_MS
        while self.speed_tier < tier:
            self.speed_tier += 1
            self.move_interval = max(MIN_MOVE_INTERVAL, self.move_interval - RAMP_STEP)
        for e in self.enemies:
            e.move_interval = self.move_interval

    # ---- Task 3 ----
    def _update_freeze(self):
        # Count down first, so a fresh pickup keeps the full 300 frames.
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            if self.freeze_timer == 0:
                for e in self.enemies:
                    e.frozen = False
        if self.pellet.active and self.player.rect.colliderect(self.pellet.rect):
            self.pellet.active = False
            self.freeze_timer = FREEZE_FRAMES
            for e in self.enemies:
                e.frozen = True

    def update(self):
        if self.caught or self.won: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.wall_rects)

        self._update_difficulty()
        self._update_freeze()
        for e in self.enemies:                                   # Task 1: each enemy runs its own BFS
            e.update(self.walls, self.player, ROWS, COLS)

        self.score += 1                                          # Task 4: +1 per frame alive

        if any(self.player.rect.colliderect(e.rect) for e in self.enemies):
            self.caught = True
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc = (50, 40, 60)
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * CELL, r * CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, wc, (x, y), (x + CELL, y), 3)
                if w[1]: pygame.draw.line(self.screen, wc, (x, y + CELL), (x + CELL, y + CELL), 3)
                if w[2]: pygame.draw.line(self.screen, wc, (x + CELL, y), (x + CELL, y + CELL), 3)
                if w[3]: pygame.draw.line(self.screen, wc, (x, y), (x, y + CELL), 3)
        pygame.draw.rect(self.screen, (80, 200, 80), self.exit_rect, border_radius=4)
        lbl = self.exit_font.render("EXIT", True, (20, 80, 20))
        self.screen.blit(lbl, lbl.get_rect(center=self.exit_rect.center))
        self.pellet.draw(self.screen)
        self.player.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        self._draw_hud()
        if self.caught:
            self._overlay("CAUGHT!", (220, 60, 60))
        if self.won:
            self._overlay("ESCAPED!", (80, 220, 80))
        pygame.display.flip()

    def _draw_hud(self):
        hud = pygame.Rect(0, ROWS * CELL, WIDTH, 50)
        pygame.draw.rect(self.screen, (30, 30, 50), hud)
        y = ROWS * CELL
        line1 = f"Survived: {self.score // 60}s   Speed Tier: {self.speed_tier}"
        self.screen.blit(self.hud_font.render(line1, True, (230, 230, 230)), (8, y + 5))
        if self.freeze_timer > 0:
            line2 = f"FROZEN! {self.freeze_timer / 60:.1f}s left"
            color = (120, 200, 255)
        elif self.pellet.active:
            line2 = "Grab the yellow pellet to freeze enemies | R=Restart"
            color = (200, 200, 120)
        else:
            line2 = "Reach EXIT before the enemies catch you! | R=Restart"
            color = (180, 180, 180)
        self.screen.blit(self.hint_font.render(line2, True, color), (8, y + 30))

    def _overlay(self, text, color):
        surf = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 140))
        self.screen.blit(surf, (0, 0))
        msg = self.big_font.render(text, True, color)
        score = self.font.render(f"Final Score: {self.score}  ({self.score // 60}s survived)", True, (255, 255, 255))
        sub = self.font.render("Press R to Restart", True, (200, 200, 200))
        cy = ROWS * CELL // 2
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, cy - 45))
        self.screen.blit(score, (WIDTH // 2 - score.get_width() // 2, cy + 5))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, cy + 35))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()