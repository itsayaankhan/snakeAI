"""
Snake (Phase 1) — human-playable, grid-based, pygame.

Run:  pip install pygame
Then: python main.py
"""

from __future__ import annotations

import random
import sys
from collections import deque
from typing import Deque, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constants — tweak grid size and speed here
# ---------------------------------------------------------------------------

GRID_WIDTH = 15
GRID_HEIGHT = 15
CELL_SIZE = 40  # pixels per grid cell
FPS = 15  # game steps per second (one cell move per step)

# Colors (R, G, B)
COLOR_BG = (30, 30, 35)
COLOR_GRID = (50, 50, 58)
COLOR_SNAKE = (80, 200, 120)
COLOR_SNAKE_HEAD = (120, 255, 160)
COLOR_FOOD = (220, 90, 90)
COLOR_TEXT = (200, 200, 200)

# Directions as (dx, dy) in grid cells per step
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Opposite pairs: used to block instant 180° turns
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

Point = Tuple[int, int]


# =============================================================================
# Game logic (no pygame) — SnakeGame
# =============================================================================


class SnakeGame:
    """
    Grid snake rules only. Rendering happens in main via read-only state.
    """

    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.snake: Deque[Point] = deque()
        self.direction: Point = RIGHT
        self.food: Point = (0, 0)
        self.score = 0
        self.game_over = False
        self.reset()

    def reset(self) -> None:
        """Start a new game: snake in center, one segment, random food."""
        self.game_over = False
        self.score = 0
        cx, cy = self.width // 2, self.height // 2
        self.snake = deque([(cx, cy)])
        self.direction = RIGHT
        self.spawn_food()

    def spawn_food(self) -> None:
        """Place food on a random empty cell (never on the snake)."""
        occupied = set(self.snake)
        empty = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in occupied
        ]
        if not empty:
            # Snake fills the board (win edge case) — no place for food
            self.food = (-1, -1)
            return
        self.food = random.choice(empty)

    def _would_reverse(self, new_dir: Point) -> bool:
        """True if new_dir is opposite of current movement (illegal)."""
        return new_dir == OPPOSITE.get(self.direction, (0, 0))

    def step(self, desired_direction: Optional[Point] = None) -> None:
        """
        One game tick: optionally update direction, then move one cell.

        desired_direction: from keyboard (WASD / arrows), or None to keep going.
        """
        if self.game_over:
            return

        if desired_direction is not None and not self._would_reverse(desired_direction):
            self.direction = desired_direction

        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        if self.check_collision(new_head):
            self.game_over = True
            return

        self.snake.appendleft(new_head)

        if new_head == self.food:
            self.score += 1
            self.spawn_food()
        else:
            self.snake.pop()

    def check_collision(self, head: Point) -> bool:
        """
        Wall or self collision for the given head position.
        (Called with the *new* head before it is added.)
        """
        x, y = head
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        # Hitting any segment is bad, except stepping into the tail cell: the
        # tail moves away this same step (unless we eat and grow — food is never
        # on the snake, so we never "eat" the tail cell).
        if head in self.snake:
            if head == self.snake[-1] and head != self.food:
                return False
            return True
        return False

    @property
    def head(self) -> Point:
        return self.snake[0]


# =============================================================================
# Pygame rendering (reads game state only)
# =============================================================================


def draw_game(surface: pygame.Surface, game: SnakeGame) -> None:
    """Draw grid, snake, food, and a tiny hint when game is over."""
    surface.fill(COLOR_BG)
    pw = game.width * CELL_SIZE
    ph = game.height * CELL_SIZE

    # Optional grid lines
    for x in range(0, pw + 1, CELL_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (x, 0), (x, ph))
    for y in range(0, ph + 1, CELL_SIZE):
        pygame.draw.line(surface, COLOR_GRID, (0, y), (pw, y))

    # Food
    if game.food[0] >= 0:
        fx, fy = game.food
        rect = pygame.Rect(fx * CELL_SIZE, fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, COLOR_FOOD, rect.inflate(-4, -4), border_radius=4)

    # Snake (head slightly different)
    for i, (sx, sy) in enumerate(game.snake):
        rect = pygame.Rect(sx * CELL_SIZE, sy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        color = COLOR_SNAKE_HEAD if i == 0 else COLOR_SNAKE
        pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=3)

    if game.game_over:
        font = pygame.font.Font(None, 28)
        msg = font.render("Game over — R to restart", True, COLOR_TEXT)
        surface.blit(msg, (8, ph + 4))


def key_to_direction(key: int) -> Optional[Point]:
    """Map pygame key constants to a direction, or None."""
    if key in (pygame.K_UP, pygame.K_w):
        return UP
    if key in (pygame.K_DOWN, pygame.K_s):
        return DOWN
    if key in (pygame.K_LEFT, pygame.K_a):
        return LEFT
    if key in (pygame.K_RIGHT, pygame.K_d):
        return RIGHT
    return None


# =============================================================================
# Main — event → update → draw loop
# =============================================================================


def main() -> None:
    pygame.init()

    game = SnakeGame()
    window_w = GRID_WIDTH * CELL_SIZE
    window_h = GRID_HEIGHT * CELL_SIZE + 36  # room for game-over text
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption("Snake — WASD / Arrows")
    clock = pygame.time.Clock()

    # Direction requested this frame (may be None = keep current)
    pending_dir: Optional[Point] = None

    running = True
    was_game_over = False
    while running:
        # --- Events: keyboard only affects pending_dir / quit / restart ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game.reset()
                    pending_dir = None
                else:
                    d = key_to_direction(event.key)
                    if d is not None:
                        pending_dir = d

        # --- Update: fixed rate, one step per frame ---
        if not game.game_over:
            game.step(pending_dir)
        pending_dir = None

        # --- Draw ---
        draw_game(screen, game)
        pygame.display.flip()
        clock.tick(FPS)

        # Print once when the game transitions to game over (not every frame).
        if game.game_over and not was_game_over:
            print(f"Game over. Score: {game.score}")
        was_game_over = game.game_over

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
