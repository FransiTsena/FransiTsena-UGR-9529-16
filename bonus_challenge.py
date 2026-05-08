import OpenGL
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
OpenGL.CONTEXT_CHECKING = False

import pygame
import random
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Constants
MAZE_ROWS = 20
MAZE_COLS = 20
WINDOW_SIZE = (800, 850)

class BonusMaze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.north_walls = [[1 for _ in range(cols + 1)] for _ in range(rows + 1)]
        self.east_walls = [[1 for _ in range(cols + 1)] for _ in range(rows + 1)]
        self.visited = [[False for _ in range(cols + 1)] for _ in range(rows + 1)]
        self.start_cell = (1, 1)
        self.end_cell = (rows, cols)
        self.path = []
        self.dead_ends = set()
        self.current_pos = None

    def draw(self):
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.1, 0.1, 0.1) # Dark gray walls
        for r in range(self.rows + 1):
            for c in range(1, self.cols + 1):
                if self.north_walls[r][c]:
                    glVertex2f(c-1, r); glVertex2f(c, r)
        for r in range(1, self.rows + 1):
            for c in range(self.cols + 1):
                if self.east_walls[r][c]:
                    glVertex2f(c, r-1); glVertex2f(c, r)
        glEnd()

    def generate_with_cycles(self):
        stack = []
        r, c = random.randint(1, self.rows), random.randint(1, self.cols)
        self.visited[r][c] = True
        total = self.rows * self.cols
        count = 1
        while count < total:
            neighbors = []
            if r < self.rows and not self.visited[r+1][c]: neighbors.append(('U', r+1, c))
            if r > 1 and not self.visited[r-1][c]: neighbors.append(('D', r-1, c))
            if c > 1 and not self.visited[r][c-1]: neighbors.append(('L', r, c-1))
            if c < self.cols and not self.visited[r][c+1]: neighbors.append(('R', r, c+1))
            if neighbors:
                dir, nr, nc = random.choice(neighbors)
                stack.append((r, c))
                if random.random() < 0.10: self._remove_random_wall(r, c)
                if dir == 'U': self.north_walls[r][c] = 0
                elif dir == 'D': self.north_walls[r-1][c] = 0
                elif dir == 'L': self.east_walls[r][c-1] = 0
                elif dir == 'R': self.east_walls[r][c] = 0
                r, c = nr, nc
                self.visited[r][c] = True
                count += 1
                yield
            elif stack:
                r, c = stack.pop()
                yield

    def _remove_random_wall(self, r, c):
        options = []
        if r < self.rows: options.append(('N', r, c))
        if r > 1: options.append(('N', r-1, c))
        if c < self.cols: options.append(('E', r, c))
        if c > 1: options.append(('E', r, c-1))
        if options:
            t, wr, wc = random.choice(options)
            if t == 'N': self.north_walls[wr][wc] = 0
            else: self.east_walls[wr][wc] = 0

    def backtracker_solver(self):
        stack = [(self.start_cell[0], self.start_cell[1], [])]
        visited = set()
        self.dead_ends = set()
        while stack:
            r, c, path = stack[-1]
            visited.add((r, c))
            self.current_pos = (r, c)
            self.path = path + [(r, c)]
            if (r, c) == self.end_cell: yield; return
            adj = []
            if r < self.rows and self.north_walls[r][c] == 0 and (r+1, c) not in visited: adj.append((r+1, c))
            if r > 1 and self.north_walls[r-1][c] == 0 and (r-1, c) not in visited: adj.append((r-1, c))
            if c > 1 and self.east_walls[r][c-1] == 0 and (r, c-1) not in visited: adj.append((r, c-1))
            if c < self.cols and self.east_walls[r][c] == 0 and (r, c+1) not in visited: adj.append((r, c+1))
            if adj:
                nr, nc = random.choice(adj)
                stack.append((nr, nc, self.path))
            else:
                self.dead_ends.add((r, c))
                stack.pop()
            yield

    def wall_follower_solver(self):
        r, c = self.start_cell
        facing = 0 # 0=Up, 1=Right, 2=Down, 3=Left
        self.path = [(r, c)]
        limit = 4000 
        steps = 0
        while (r, c) != self.end_cell and steps < limit:
            self.current_pos = (r, c)
            self.path.append((r, c))
            steps += 1
            for turn in [-1, 0, 1, 2]:
                new_facing = (facing + turn) % 4
                can_move, nr, nc = False, r, c
                if new_facing == 0:
                    if r < self.rows and self.north_walls[r][c] == 0: can_move, nr, nc = True, r+1, c
                elif new_facing == 1:
                    if c < self.cols and self.east_walls[r][c] == 0: can_move, nr, nc = True, r, c+1
                elif new_facing == 2:
                    if r > 1 and self.north_walls[r-1][c] == 0: can_move, nr, nc = True, r-1, c
                elif new_facing == 3:
                    if c > 1 and self.east_walls[r][c-1] == 0: can_move, nr, nc = True, r, c-1
                if can_move:
                    r, c = nr, nc
                    facing = new_facing
                    break
            yield

def main():
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("BONUS CHALLENGE: Backtracking vs Wall-Follower")
    glClearColor(1.0, 1.0, 1.0, 1.0) # White background
    gluOrtho2D(0.0, MAZE_COLS, -5.0, MAZE_ROWS)
    
    maze = BonusMaze(MAZE_ROWS, MAZE_COLS)
    gen = maze.generate_with_cycles()
    solver = None
    state = "GENERATING"
    solver_type = "NONE"
    clock = pygame.time.Clock()

    while True:
        try:
            glGetError()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: 
                        solver_type = "BACKTRACKER"
                        maze.path = []; maze.dead_ends = set(); solver = maze.backtracker_solver()
                    if event.key == pygame.K_2: 
                        solver_type = "WALL_FOLLOWER"
                        maze.path = []; maze.dead_ends = set(); solver = maze.wall_follower_solver()
        except: pass

        if state == "GENERATING":
            try: next(gen)
            except StopIteration:
                maze.start_cell = (MAZE_ROWS//2, MAZE_COLS//2)
                maze.end_cell = (MAZE_ROWS, MAZE_COLS)
                state = "READY"
                # Auto-start with the Smart Backtracker
                solver_type = "BACKTRACKER"
                solver = maze.backtracker_solver()
        elif solver:
            try: next(solver)
            except StopIteration: solver = None

        glClear(GL_COLOR_BUFFER_BIT)
        maze.draw()
        
        glPointSize(15.0)
        glBegin(GL_POINTS)
        glColor3f(0, 0.8, 0); glVertex2f(maze.start_cell[1]-0.5, maze.start_cell[0]-0.5)
        glColor3f(0.8, 0, 0.8); glVertex2f(maze.end_cell[1]-0.5, maze.end_cell[0]-0.5)
        glEnd()

        glPointSize(8.0)
        glBegin(GL_POINTS)
        glColor3f(1, 0, 0)
        for p in maze.path: glVertex2f(p[1]-0.5, p[0]-0.5)
        glEnd()

        glColor3f(0, 0, 1)
        glBegin(GL_POINTS)
        for d in maze.dead_ends: glVertex2f(d[1]-0.5, d[0]-0.5)
        glEnd()

        msg = f"Mode: {solver_type} | Press 1: Smart Backtracker | Press 2: Dumb Wall-Follower"
        pygame.display.set_caption(msg)
        pygame.display.flip()
        clock.tick(120 if state == "GENERATING" else 40)

if __name__ == "__main__":
    main()
