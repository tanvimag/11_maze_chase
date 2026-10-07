"""Headless tests for Maze Chase. Run with:  python -m unittest tests.test_game -v"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import unittest
from unittest import mock
import pygame

from game import game_engine as ge
from game.game_engine import GameEngine, ROWS, COLS, FREEZE_FRAMES
from game.maze import CELL


class NoKeys:
    def __getitem__(self, k): return False


class MazeChaseTests(unittest.TestCase):
    def setUp(self):
        self.g = GameEngine()

    def tearDown(self):
        pygame.quit()

    # Bug fix
    def test_player_cannot_walk_through_walls(self):
        g = self.g
        # Hold "right" for a long time: the player must never leave the start cell
        # if there is a wall on its right, and never cross any wall in general.
        class Right:
            def __getitem__(self, k): return k in (pygame.K_RIGHT,)
        for _ in range(2000):
            g.player.move(Right(), g.wall_rects)
            self.assertEqual(g.player.rect.collidelist(g.wall_rects), -1)
        # can't pass a closed outer boundary
        self.assertLess(g.player.rect.right, COLS * CELL + 1)

    # Task 1
    def test_three_enemies_in_different_corners(self):
        g = self.g
        self.assertEqual(len(g.enemies), 3)
        corners = {(e.r, e.c) for e in g.enemies}
        self.assertEqual(corners, {(ROWS-1, COLS-1), (0, COLS-1), (ROWS-1, 0)})

    def test_each_enemy_calls_bfs_independently(self):
        g = self.g
        with mock.patch("game.entities.bfs", return_value=None) as m:
            for e in g.enemies: e.timer = e.move_interval  # force a move on next update
            for e in g.enemies: e.update(g.walls, g.player, ROWS, COLS)
            self.assertEqual(m.call_count, 3)

    def test_enemies_actually_chase(self):
        g = self.g
        start = [(e.r, e.c) for e in g.enemies]
        for _ in range(60):
            for e in g.enemies: e.update(g.walls, g.player, ROWS, COLS)
        self.assertTrue(all((e.r, e.c) != s for e, s in zip(g.enemies, start)))

    # Task 2
    def test_speed_ramps_every_15s_with_floor_of_5(self):
        g = self.g
        t0 = g.start_ticks
        with mock.patch("pygame.time.get_ticks", return_value=t0 + 14_999):
            g._update_difficulty(); self.assertEqual(g.enemies[0].move_interval, 20)
        with mock.patch("pygame.time.get_ticks", return_value=t0 + 15_000):
            g._update_difficulty(); self.assertEqual(g.enemies[0].move_interval, 18)
        with mock.patch("pygame.time.get_ticks", return_value=t0 + 30_000):
            g._update_difficulty(); self.assertEqual(g.enemies[2].move_interval, 16)
        with mock.patch("pygame.time.get_ticks", return_value=t0 + 10 * 60_000):
            g._update_difficulty()
            self.assertTrue(all(e.move_interval == 5 for e in g.enemies))

    # Task 3
    def test_pellet_freezes_enemies_for_300_frames(self):
        g = self.g
        g.player.rect.center = g.pellet.rect.center
        g._update_freeze()
        self.assertFalse(g.pellet.active)
        self.assertTrue(all(e.frozen for e in g.enemies))
        self.assertEqual(g.freeze_timer, FREEZE_FRAMES)
        # frozen enemies don't move
        before = [(e.r, e.c) for e in g.enemies]
        for _ in range(100):
            for e in g.enemies: e.update(g.walls, g.player, ROWS, COLS)
            g._update_freeze()
        self.assertEqual(before, [(e.r, e.c) for e in g.enemies])
        for _ in range(FREEZE_FRAMES):
            g._update_freeze()
        self.assertTrue(all(not e.frozen for e in g.enemies))

    def test_pellet_not_on_spawn_or_exit(self):
        for _ in range(200):
            g = GameEngine()
            self.assertNotIn((g.pellet.r, g.pellet.c),
                             {(0,0),(ROWS-1,COLS-1),(0,COLS-1),(ROWS-1,0),(ROWS//2,COLS//2)})

    # Task 4
    def test_score_increments_each_frame_and_stops_on_game_over(self):
        g = self.g
        with mock.patch("pygame.key.get_pressed", return_value=NoKeys()):
            for _ in range(5): g.update()
            self.assertEqual(g.score, 5)
            g.caught = True
            g.update()
            self.assertEqual(g.score, 5)

    def test_reset_clears_state(self):
        g = self.g
        g.score = 999; g.caught = True; g.freeze_timer = 50; g.speed_tier = 3
        g.reset()
        self.assertEqual((g.score, g.caught, g.freeze_timer, g.speed_tier), (0, False, 0, 0))

    def test_draw_all_states_without_error(self):
        g = self.g
        g.draw()
        g.freeze_timer = 120
        for e in g.enemies: e.frozen = True
        g.draw()
        g.caught = True; g.draw()
        g.caught = False; g.won = True; g.draw()


if __name__ == "__main__":
    unittest.main()