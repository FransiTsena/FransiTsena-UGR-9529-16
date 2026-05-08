import OpenGL
OpenGL.ERROR_CHECKING = False

import pygame
import random
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Constants
MAZE_ROWS = 20
MAZE_COLS = 20
WINDOW_SIZE = (600, 600)
FPS = 60

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        # Walls: 1 = wall exists, 0 = wall removed
        self.north_walls = [[1 for _ in range(cols + 1)] for _ in range(rows + 1)]
        self.east_walls = [[1 for _ in range(cols + 1)] for _ in range(rows + 1)]
        self.visited = [[False for _ in range(cols + 1)] for _ in range(rows + 1)]
        
        self.start_cell = (1, 1)
        self.end_cell = (rows, cols)
        self.path = []
        self.dead_ends = set()
        self.current_pos = None

    def draw(self):
        """Draws the maze walls using OpenGL."""
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.1, 0.1, 0.1)  # Dark gray walls
        
        # Draw north walls
        for r in range(self.rows + 1):
            for c in range(1, self.cols + 1):
                if self.north_walls[r][c]:
                    glVertex2f(c - 1, r)
                    glVertex2f(c, r)
                    
        # Draw east walls
        for r in range(1, self.rows + 1):
            for c in range(self.cols + 1):
                if self.east_walls[r][c]:
                    glVertex2f(c, r - 1)
                    glVertex2f(c, r)
        glEnd()

    def draw_cell_marker(self, r, c, color, size=12.0):
        """Draws a point marker in a cell."""
        glPointSize(size)
        glBegin(GL_POINTS)
        glColor3f(*color)
        glVertex2f(c - 0.5, r - 0.5)
        glEnd()

    def generate_generator(self):
        """Generator that yields during maze creation for animation."""
        stack = []
        curr_r, curr_c = random.randint(1, self.rows), random.randint(1, self.cols)
        self.visited[curr_r][curr_c] = True
        total_cells = self.rows * self.cols
        visited_count = 1
        
        while visited_count < total_cells:
            neighbors = []
            # Up, Down, Left, Right
            if curr_r < self.rows and not self.visited[curr_r + 1][curr_c]:
                neighbors.append(('U', curr_r + 1, curr_c))
            if curr_r > 1 and not self.visited[curr_r - 1][curr_c]:
                neighbors.append(('D', curr_r - 1, curr_c))
            if curr_c > 1 and not self.visited[curr_r][curr_c - 1]:
                neighbors.append(('L', curr_r, curr_c - 1))
            if curr_c < self.cols and not self.visited[curr_r][curr_c + 1]:
                neighbors.append(('R', curr_r, curr_c + 1))
                
            if neighbors:
                direction, next_r, next_c = random.choice(neighbors)
                stack.append((curr_r, curr_c))
                
                # Remove wall between current and next
                if direction == 'U': self.north_walls[curr_r][curr_c] = 0
                elif direction == 'D': self.north_walls[curr_r - 1][curr_c] = 0
                elif direction == 'L': self.east_walls[curr_r][curr_c - 1] = 0
                elif direction == 'R': self.east_walls[curr_r][curr_c] = 0
                
                curr_r, curr_c = next_r, next_c
                self.visited[curr_r][curr_c] = True
                visited_count += 1
                yield
            elif stack:
                curr_r, curr_c = stack.pop()
                yield

    def pick_start_end_on_edges(self):
        """Randomly selects start and end points on the maze boundaries."""
        edges = []
        for c in range(1, self.cols + 1):
            edges.append((1, c))
            edges.append((self.rows, c))
        for r in range(1, self.rows + 1):
            edges.append((r, 1))
            edges.append((r, self.cols))
            
        self.start_cell = random.choice(edges)
        self.end_cell = random.choice(edges)
        while self.end_cell == self.start_cell:
            self.end_cell = random.choice(edges)
            
        # Open the outer walls for entry/exit
        self._open_boundary_wall(self.start_cell)
        self._open_boundary_wall(self.end_cell)

    def _open_boundary_wall(self, cell):
        r, c = cell
        if r == 1: self.north_walls[0][c] = 0
        elif r == self.rows: self.north_walls[self.rows][c] = 0
        elif c == 1: self.east_walls[r][0] = 0
        elif c == self.cols: self.east_walls[r][self.cols] = 0

    def solve_generator(self):
        """Generator that yields during maze solving for animation."""
        stack = [(self.start_cell[0], self.start_cell[1], [])]
        visited_solve = set()
        self.dead_ends = set()
        
        while stack:
            r, c, path = stack[-1]
            visited_solve.add((r, c))
            self.current_pos = (r, c)
            self.path = path + [(r, c)]
            
            if (r, c) == self.end_cell:
                yield
                return

            neighbors = []
            # Check for passages (walls == 0) and unvisited cells
            if r < self.rows and self.north_walls[r][c] == 0 and (r + 1, c) not in visited_solve:
                neighbors.append((r + 1, c))
            if r > 1 and self.north_walls[r - 1][c] == 0 and (r - 1, c) not in visited_solve:
                neighbors.append((r - 1, c))
            if c > 1 and self.east_walls[r][c - 1] == 0 and (r, c - 1) not in visited_solve:
                neighbors.append((r, c - 1))
            if c < self.cols and self.east_walls[r][c] == 0 and (r, c + 1) not in visited_solve:
                neighbors.append((r, c + 1))
                
            if neighbors:
                next_r, next_c = random.choice(neighbors)
                stack.append((next_r, next_c, self.path))
            else:
                self.dead_ends.add((r, c))
                stack.pop()
            yield

def main():
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Maze Generator and Solver")
    
    glClearColor(0.95, 0.95, 0.95, 1.0)  # Light background
    gluOrtho2D(0.0, MAZE_COLS, 0.0, MAZE_ROWS)
    
    maze = Maze(MAZE_ROWS, MAZE_COLS)
    
    gen_iterator = maze.generate_generator()
    solve_iterator = None
    
    state = "GENERATING"  # States: GENERATING, SOLVING, DONE
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update Logic
        if state == "GENERATING":
            try:
                next(gen_iterator)
            except StopIteration:
                maze.pick_start_end_on_edges()
                solve_iterator = maze.solve_generator()
                state = "SOLVING"
        elif state == "SOLVING":
            try:
                next(solve_iterator)
            except StopIteration:
                state = "DONE"

        # Rendering
        glClear(GL_COLOR_BUFFER_BIT)
        maze.draw()
        
        # Draw markers
        for de in maze.dead_ends:
            maze.draw_cell_marker(de[0], de[1], (0.7, 0.7, 1.0), 8.0) # Light blue dead ends
            
        for p in maze.path:
            maze.draw_cell_marker(p[0], p[1], (1.0, 0.3, 0.3), 10.0) # Soft red path
            
        if maze.current_pos:
            maze.draw_cell_marker(maze.current_pos[0], maze.current_pos[1], (0.8, 0.0, 0.0), 14.0) # Active head

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
