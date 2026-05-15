import pygame
import math
import random

WIDTH = 800
ROWS = 40
WIN = pygame.display.set_mode((WIDTH, WIDTH))
pygame.display.set_caption("Multi-Path Curved Graph Visualizer")

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

def get_valid_neighbors(r, c, visited):
    neighbors = []
    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < ROWS and (nr, nc) not in visited:
            neighbors.append((nr, nc))
    return neighbors

def clean_temporary_search_colors(grid, temp_colored):
    for r, c in temp_colored:
        if grid[r][c].color == YELLOW:
            grid[r][c].color = BLACK

def find_all_paths_from_node(draw_func, grid, start_node, target_nodes):
    stack = [(start_node.r, start_node.c, 0, {(start_node.r, start_node.c)})]
    found_paths = []
    temp_colored = set()
    
    while stack:
        pygame.event.pump()
        r, c, dist, visited = stack.pop()
        
        is_target = False
        for t in target_nodes:
            if t != start_node and t.r == r and t.c == c:
                found_paths.append((t, dist))
                is_target = True
                break
        
        if is_target:
            continue
            
        for nr, nc in get_valid_neighbors(r, c, visited):
            neighbor = grid[nr][nc]
            if neighbor.color == BLACK or neighbor in target_nodes:
                new_visited = set(visited)
                new_visited.add((nr, nc))
                stack.append((nr, nc, dist + 1, new_visited))
                
                if neighbor.color == BLACK:
                    neighbor.color = YELLOW
                    temp_colored.add((nr, nc))
        draw_func()
        
    clean_temporary_search_colors(grid, temp_colored)
    draw_func()
    return found_paths

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

def group_raw_paths_into_graph_data(raw_paths):
    graph_data = {}
    for s, e, d in raw_paths:
        if (s, e) not in graph_data:
            graph_data[(s, e)] = []
        graph_data[(s, e)].append(d)
    return graph_data

def execute_path_search(grid, target_nodes, mode):
    raw_paths = set()
    draw_callback = lambda: render_screen(WIN, grid, mode, {}, target_nodes)
    
    for start_node in target_nodes:
        paths = find_all_paths_from_node(draw_callback, grid, start_node, target_nodes)
        for end_node, dist in paths:
            if id(start_node) < id(end_node):
                raw_paths.add((start_node, end_node, dist))
            else:
                raw_paths.add((end_node, start_node, dist))
                
    return group_raw_paths_into_graph_data(raw_paths)

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