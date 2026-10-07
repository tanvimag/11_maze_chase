import pygame
from game.maze import CELL, bfs

SPEED = 2


class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2
        self.rect = pygame.Rect(cx - 10, cy - 10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, wall_rects):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = SPEED
        # Move one axis at a time so the player can slide along walls.
        nr = self.rect.move(dx, 0)
        if self._valid(nr, wall_rects): self.rect = nr
        nr = self.rect.move(0, dy)
        if self._valid(nr, wall_rects): self.rect = nr

    def _valid(self, rect, wall_rects):
        # BUG FIX: the original only checked the screen bounds, so the player
        # walked through maze walls. Now we collide against the wall rects.
        return rect.collidelist(wall_rects) == -1

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)


class Enemy:
    NORMAL_COLOR = (220, 60, 60)
    FROZEN_COLOR = (140, 200, 240)

    def __init__(self, r, c, timer_offset=0):
        self.r, self.c = r, c
        cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2
        self.rect = pygame.Rect(cx - 12, cy - 12, 24, 24)
        self.color = self.NORMAL_COLOR
        self.timer = timer_offset      # staggered so enemies don't move in lock-step
        self.move_interval = 20        # frames between cell moves
        self.frozen = False            # Task 3: set by the engine when a pellet is eaten

    def update(self, walls, player, rows, cols):
        if self.frozen:                # Task 3: frozen enemies do nothing
            return
        self.timer += 1
        if self.timer >= self.move_interval:
            self.timer = 0
            pr, pc = player.rect.centery // CELL, player.rect.centerx // CELL
            step = bfs(walls, (self.r, self.c), (pr, pc), rows, cols)
            if step:
                dr, dc = step
                self.r += dr; self.c += dc
                cx, cy = self.c * CELL + CELL // 2, self.r * CELL + CELL // 2
                self.rect.center = (cx, cy)

    def draw(self, screen):
        color = self.FROZEN_COLOR if self.frozen else self.NORMAL_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        # eyes
        for ex in [self.rect.x + 4, self.rect.x + 14]:
            pygame.draw.circle(screen, (255, 255, 255), (ex, self.rect.y + 8), 4)
            pygame.draw.circle(screen, (0, 0, 0), (ex + 1, self.rect.y + 8), 2)
        if self.frozen:                # Task 3: visible frozen indicator
            pygame.draw.rect(screen, (40, 110, 200), self.rect.inflate(6, 6), 2, border_radius=7)
            cx, cy = self.rect.centerx, self.rect.bottom - 5
            for dx, dy in [(-4, 0), (4, 0), (0, -3), (0, 3)]:    # little "ice cross"
                pygame.draw.line(screen, (255, 255, 255), (cx, cy), (cx + dx, cy + dy), 1)


class PowerPellet:
    """Task 3: yellow circle; touching it freezes all enemies."""
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c * CELL + CELL // 2, r * CELL + CELL // 2
        self.radius = 9
        self.rect = pygame.Rect(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)
        self.active = True

    def draw(self, screen):
        if not self.active:
            return
        pygame.draw.circle(screen, (255, 215, 0), self.rect.center, self.radius)
        pygame.draw.circle(screen, (200, 150, 0), self.rect.center, self.radius, 2)