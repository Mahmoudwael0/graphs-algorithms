import pygame
import math
import random

WIDTH = 800
ROWS = 40
WIN = pygame.display.set_mode((WIDTH, WIDTH))
pygame.display.set_caption("Smart Mass-Based Graph Visualizer")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREY = (220, 220, 220)
YELLOW = (255, 255, 0)
NODE_COLORS = [(255, 0, 0), (128, 0, 128), (0, 0, 255), (255, 165, 0), (255, 20, 147)]

class Node:
    def __init__(self, r, c, w):
        self.r = r
        self.c = c
        self.x = r * w
        self.y = c * w
        self.color = WHITE
        self.width = w

    def draw(self, win, mode):
        if mode == "grid":
            pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))
        elif self.color in NODE_COLORS:
            pygame.draw.circle(win, self.color, (self.x + self.width//2, self.y + self.width//2), self.width)

def initialize_grid():
    return [[Node(i, j, WIDTH//ROWS) for j in range(ROWS)] for i in range(ROWS)]

def render_distance_label(win, dist, pos, font):
    label = font.render(str(dist), True, RED)
    label_rect = label.get_rect(center=pos)
    pygame.draw.rect(win, WHITE, label_rect)
    win.blit(label, label_rect)

def draw_straight_connection(win, start_pos, end_pos, dist, font):
    pygame.draw.line(win, BLACK, start_pos, end_pos, 3)
    label_pos = ((start_pos[0] + end_pos[0]) // 2, (start_pos[1] + end_pos[1]) // 2)
    render_distance_label(win, dist, label_pos, font)

def draw_curved_connection(win, start_pos, end_pos, dist, offset, font):
    x1, y1 = start_pos
    x2, y2 = end_pos
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    
    if length == 0: 
        return
        
    nx, ny = -dy / length, dx / length
    cx = mx + nx * offset
    cy = my + ny * offset
    
    points = []
    for step in range(21):
        t = step / 20.0
        u = 1 - t
        px = u * u * x1 + 2 * u * t * cx + t * t * x2
        py = u * u * y1 + 2 * u * t * cy + t * t * y2
        points.append((int(px), int(py)))
        
    pygame.draw.lines(win, BLACK, False, points, 3)
    label_pos = (int(0.25 * x1 + 0.5 * cx + 0.25 * x2), int(0.25 * y1 + 0.5 * cy + 0.25 * y2))
    render_distance_label(win, dist, label_pos, font)

def generate_curve_offsets(num_paths):
    offsets = []
    if num_paths % 2 != 0:
        offsets.append(0)
    for i in range(1, num_paths // 2 + 1):
        offsets.append(i * 50)
        offsets.append(-i * 50)
    return offsets

def draw_graph_connections(win, graph_data):
    font = pygame.font.SysFont('Arial', 20, bold=True)
    for (s_node, e_node), distances in graph_data.items():
        start_pos = (s_node.x + s_node.width // 2, s_node.y + s_node.width // 2)
        end_pos = (e_node.x + e_node.width // 2, e_node.y + e_node.width // 2)
        
        distances.sort()
        offsets = generate_curve_offsets(len(distances))
            
        for i, dist in enumerate(distances):
            if offsets[i] == 0:
                draw_straight_connection(win, start_pos, end_pos, dist, font)
            else:
                draw_curved_connection(win, start_pos, end_pos, dist, offsets[i], font)

def draw_grid_lines(win):
    gap = WIDTH // ROWS
    for i in range(ROWS):
        pygame.draw.line(win, GREY, (0, i * gap), (WIDTH, i * gap))
        pygame.draw.line(win, GREY, (i * gap, 0), (i * gap, WIDTH))

def render_screen(win, grid, mode, graph_data, target_nodes):
    win.fill(WHITE)
    if mode == "grid":
        for row in grid:
            for n in row: 
                n.draw(win, "grid")
        draw_grid_lines(win)
    else:
        draw_graph_connections(win, graph_data)
        for n in target_nodes: 
            n.draw(win, "graph")
    pygame.display.update()

def handle_mouse_clicks(grid, target_nodes):
    m_p = pygame.mouse.get_pressed()
    pos = pygame.mouse.get_pos()
    r, c = pos[0] // (WIDTH // ROWS), pos[1] // (WIDTH // ROWS)
    
    if 0 <= r < ROWS and 0 <= c < ROWS:
        node = grid[r][c]
        if m_p[0] and node.color == WHITE and len(target_nodes) < 5:
            node.color = NODE_COLORS[len(target_nodes)]
            target_nodes.append(node)
        elif m_p[2] and node.color == WHITE:
            node.color = BLACK

def execute_path_search(grid, target_nodes, mode):
    graph_data = {}
    visited_black_squares = set()
    draw_callback = lambda: render_screen(WIN, grid, mode, {}, target_nodes)
    
    for r in range(ROWS):
        for c in range(ROWS):
            if grid[r][c].color == BLACK and (r, c) not in visited_black_squares:
                wire_squares = []
                touched_nodes = set()
                
                queue = [(r, c)]
                visited_black_squares.add((r, c))
                grid[r][c].color = YELLOW
                draw_callback()
                
                while queue:
                    pygame.event.pump()
                    curr_r, curr_c = queue.pop(0)
                    wire_squares.append((curr_r, curr_c))
                    
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < ROWS and 0 <= nc < ROWS:
                            neighbor = grid[nr][nc]
                            if neighbor.color == BLACK and (nr, nc) not in visited_black_squares:
                                visited_black_squares.add((nr, nc))
                                queue.append((nr, nc))
                                neighbor.color = YELLOW
                                draw_callback()
                            elif neighbor in target_nodes:
                                touched_nodes.add(neighbor)
                                
                for wr, wc in wire_squares:
                    grid[wr][wc].color = BLACK
                draw_callback()
                
                wire_length = len(wire_squares)
                
                touched_list = list(touched_nodes)
                for i in range(len(touched_list)):
                    for j in range(i + 1, len(touched_list)):
                        n1 = touched_list[i]
                        n2 = touched_list[j]
                        
                        if id(n1) > id(n2):
                            n1, n2 = n2, n1
                            
                        pair = (n1, n2)
                        if pair not in graph_data:
                            graph_data[pair] = []
                        graph_data[pair].append(wire_length)
                        
    return graph_data

def add_random_noise(grid):
    for row in grid:
        for n in row:
            if n.color == WHITE and random.random() < 0.15: 
                n.color = BLACK

def main():
    pygame.init()
    grid = initialize_grid()
    target_nodes = []
    graph_data = {}
    mode = "grid"
    
    run = True
    while run:
        render_screen(WIN, grid, mode, graph_data, target_nodes)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                run = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g: 
                    mode = "graph" if mode == "grid" else "grid"
                    
                if event.key == pygame.K_c:
                    grid = initialize_grid()
                    target_nodes = []
                    graph_data = {}
                    mode = "grid"
                    
                if event.key == pygame.K_r:
                    add_random_noise(grid)

                if event.key == pygame.K_SPACE and mode == "grid":
                    graph_data = execute_path_search(grid, target_nodes, mode)

        if mode == "grid":
            handle_mouse_clicks(grid, target_nodes)
            
    pygame.quit()

if __name__ == "__main__":
    main()
