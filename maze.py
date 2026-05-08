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
WINDOW_SIZE = (700, 800)

class Maze:
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
        glColor3f(0.1, 0.1, 0.1)
        for r in range(self.rows + 1):
            for c in range(1, self.cols + 1):
                if self.north_walls[r][c]:
                    glVertex2f(c - 1, r)
                    glVertex2f(c, r)
        for r in range(1, self.rows + 1):
            for c in range(self.cols + 1):
                if self.east_walls[r][c]:
                    glVertex2f(c, r - 1)
                    glVertex2f(c, r)
        glEnd()

    def draw_cell_marker(self, r, c, color, size=12.0):
        glPointSize(size)
        glBegin(GL_POINTS)
        glColor3f(*color)
        glVertex2f(c - 0.5, r - 0.5)
        glEnd()

    def generate_generator(self):
        stack = []
        curr_r, curr_c = random.randint(1, self.rows), random.randint(1, self.cols)
        self.visited[curr_r][curr_c] = True
        total_cells = self.rows * self.cols
        visited_count = 1
        while visited_count < total_cells:
            neighbors = []
            if curr_r < self.rows and not self.visited[curr_r + 1][curr_c]: neighbors.append(('U', curr_r + 1, curr_c))
            if curr_r > 1 and not self.visited[curr_r - 1][curr_c]: neighbors.append(('D', curr_r - 1, curr_c))
            if curr_c > 1 and not self.visited[curr_r][curr_c - 1]: neighbors.append(('L', curr_r, curr_c - 1))
            if curr_c < self.cols and not self.visited[curr_r][curr_c + 1]: neighbors.append(('R', curr_r, curr_c + 1))
            if neighbors:
                direction, next_r, next_c = random.choice(neighbors)
                stack.append((curr_r, curr_c))
                if random.random() < 0.05: self._eat_extra_wall(curr_r, curr_c)
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

    def _eat_extra_wall(self, r, c):
        walls = []
        if r < self.rows: walls.append(('N', r, c))
        if r > 1: walls.append(('N', r-1, c))
        if c < self.cols: walls.append(('E', r, c))
        if c > 1: walls.append(('E', r, c-1))
        if walls:
            type, wr, wc = random.choice(walls)
            if type == 'N': self.north_walls[wr][wc] = 0
            else: self.east_walls[wr][wc] = 0

    def pick_interior_start_end(self):
        self.start_cell = (random.randint(2, self.rows-1), random.randint(2, self.cols-1))
        self.end_cell = (random.randint(2, self.rows-1), random.randint(2, self.cols-1))
        while self.end_cell == self.start_cell:
            self.end_cell = (random.randint(2, self.rows-1), random.randint(2, self.cols-1))

    def solve_generator(self):
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

class LegendRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont('Arial', 24)
        self.labels = ["Start", "End", "Path", "Dead End"]
        self.textures = []
        self.tex_sizes = []
        for label in self.labels:
            tex, size = self._create_text_texture(label)
            self.textures.append(tex)
            self.tex_sizes.append(size)

    def _create_text_texture(self, text):
        surf = self.font.render(text, True, (0, 0, 0), (255, 255, 255))
        data = pygame.image.tostring(surf, 'RGBA', True)
        width, height = surf.get_size()
        
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return tex, (width, height)

    def draw(self, cols, rows):
        colors = [(0, 1, 0), (1, 0, 1), (1, 0, 0), (0, 0, 1)]
        glEnable(GL_TEXTURE_2D)
        for i, (color, tex) in enumerate(zip(colors, self.textures)):
            x = 1 + (i * 5)
            y = -1.5
            
            # Draw Color Box
            glDisable(GL_TEXTURE_2D)
            glColor3f(*color)
            glBegin(GL_QUADS)
            glVertex2f(x, y - 0.4)
            glVertex2f(x + 0.8, y - 0.4)
            glVertex2f(x + 0.8, y + 0.4)
            glVertex2f(x, y + 0.4)
            glEnd()
            
            # Draw Text Label
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex)
            glColor3f(1, 1, 1) # White for texture blend
            w, h = self.tex_sizes[i]
            aspect = w / h
            label_w = 2.0 * aspect * (h / 32.0) # Scaling
            label_h = 1.0
            
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(x + 1.0, y - 0.4)
            glTexCoord2f(1, 0); glVertex2f(x + 1.0 + label_w, y - 0.4)
            glTexCoord2f(1, 1); glVertex2f(x + 1.0 + label_w, y + 0.4)
            glTexCoord2f(0, 1); glVertex2f(x + 1.0, y + 0.4)
            glEnd()
        glDisable(GL_TEXTURE_2D)

def main():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Maze Generator and Solver")
    
    glClearColor(1.0, 1.0, 1.0, 1.0)
    gluOrtho2D(0.0, MAZE_COLS, -3.0, MAZE_ROWS)
    
    legend = LegendRenderer()
    maze = Maze(MAZE_ROWS, MAZE_COLS)
    gen_iterator = maze.generate_generator()
    solve_iterator = None
    state = "GENERATING"
    clock = pygame.time.Clock()
    
    while True:
        try:
            glGetError()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
        except (SystemError, KeyError): pass

        if state == "GENERATING":
            try: next(gen_iterator)
            except StopIteration:
                maze.pick_interior_start_end()
                solve_iterator = maze.solve_generator()
                state = "SOLVING"
        elif state == "SOLVING":
            try: next(solve_iterator)
            except StopIteration: state = "DONE"

        glClear(GL_COLOR_BUFFER_BIT)
        legend.draw(MAZE_COLS, MAZE_ROWS)
        maze.draw()
        for de in maze.dead_ends: maze.draw_cell_marker(de[0], de[1], (0, 0, 1), 8.0)
        for p in maze.path: maze.draw_cell_marker(p[0], p[1], (1, 0, 0), 10.0)
        maze.draw_cell_marker(maze.start_cell[0], maze.start_cell[1], (0, 1, 0), 16.0)
        maze.draw_cell_marker(maze.end_cell[0], maze.end_cell[1], (1, 0, 1), 16.0)

        pygame.display.flip()
        if state == "GENERATING": clock.tick(120)
        else: clock.tick(20)

if __name__ == "__main__":
    main()
