import pygame
import math
width=800
rows=40
win=pygame.display.set_mode((width,width))
pygame.display.set_caption("smart mass-based graph visualizer & dev tools")
white=(255,255,255)
black=(0,0,0)
red=(255,0,0)
grey=(220,220,220)
yellow=(255,255,0)
node_colors=[(255,0,0),(128,0,128),(0,0,255),(255,165,0),(255,20,147)]
class node:
    def __init__(self,r,c,w):
        self.r=r
        self.c=c
        self.x=r*w
        self.y=c*w
        self.color=white
        self.width=w
    def draw(self,w,mode):
        if mode=="grid":
            pygame.draw.rect(w,self.color,(self.x,self.y,self.width,self.width))
        elif self.color in node_colors:
            pygame.draw.circle(w,self.color,(self.x+self.width//2,self.y+self.width//2),self.width)
def initialize_grid():
    return [[node(i,j,width//rows) for j in range(rows)] for i in range(rows)]
def render_distance_label(w,dist,pos,font):
    label=font.render(str(dist),True,red)
    label_rect=label.get_rect(center=pos)
    pygame.draw.rect(w,white,label_rect)
    w.blit(label,label_rect)
def draw_straight_connection(w,start_pos,end_pos,dist,font):
    pygame.draw.line(w,black,start_pos,end_pos,3)
    label_pos=((start_pos[0]+end_pos[0])//2,(start_pos[1]+end_pos[1])//2)
    render_distance_label(w,dist,label_pos,font)
def draw_curved_connection(w,start_pos,end_pos,dist,offset,font):
    x1,y1=start_pos
    x2,y2=end_pos
    mx,my=(x1+x2)/2,(y1+y2)/2
    dx,dy=x2-x1,y2-y1
    length=math.hypot(dx,dy)
    if length==0: return
    nx,ny=-dy/length,dx/length
    cx=mx+nx*offset
    cy=my+ny*offset
    points=[]
    for step in range(21):
        t=step/20.0
        u=1-t
        px=u*u*x1+2*u*t*cx+t*t*x2
        py=u*u*y1+2*u*t*cy+t*t*y2
        points.append((int(px),int(py)))
    pygame.draw.lines(w,black,False,points,3)
    label_pos=(int(0.25*x1+0.5*cx+0.25*x2),int(0.25*y1+0.5*cy+0.25*y2))
    render_distance_label(w,dist,label_pos,font)
def generate_curve_offsets(num_paths):
    offsets=[]
    if num_paths%2!=0: offsets.append(0)
    for i in range(1,num_paths//2+1):
        offsets.append(i*50)
        offsets.append(-i*50)
    return offsets
def draw_graph_connections(w,graph_data):
    font=pygame.font.SysFont('arial',20,bold=True)
    for (s_node,e_node),distances in graph_data.items():
        start_pos=(s_node.x+s_node.width//2,s_node.y+s_node.width//2)
        end_pos=(e_node.x+e_node.width//2,e_node.y+e_node.width//2)
        distances.sort()
        offsets=generate_curve_offsets(len(distances))
        for i,dist in enumerate(distances):
            if offsets[i]==0: draw_straight_connection(w,start_pos,end_pos,dist,font)
            else: draw_curved_connection(w,start_pos,end_pos,dist,offsets[i],font)
def draw_grid_lines(w):
    gap=width//rows
    for i in range(rows):
        pygame.draw.line(w,grey,(0,i*gap),(width,i*gap))
        pygame.draw.line(w,grey,(i*gap,0),(i*gap,width))
def render_screen(w,grid,mode,graph_data,target_nodes):
    w.fill(white)
    if mode=="grid":
        for row in grid:
            for n in row: n.draw(w,"grid")
        draw_grid_lines(w)
    else:
        draw_graph_connections(w,graph_data)
        for n in target_nodes: n.draw(w,"graph")
    pygame.display.update()
def handle_mouse_clicks(grid,target_nodes):
    m_p=pygame.mouse.get_pressed()
    pos=pygame.mouse.get_pos()
    r,c=pos[0]//(width//rows),pos[1]//(width//rows)
    if 0<=r<rows and 0<=c<rows:
        node=grid[r][c]
        if m_p[0] and node.color==white and len(target_nodes)<5:
            node.color=node_colors[len(target_nodes)]
            target_nodes.append(node)
        elif m_p[2] and node.color==white:
            node.color=black
def execute_path_search(grid,target_nodes,mode):
    graph_data={}
    visited_black_squares=set()
    draw_callback=lambda: render_screen(win,grid,mode,{},target_nodes)
    for r in range(rows):
        for c in range(rows):
            if grid[r][c].color==black and (r,c) not in visited_black_squares:
                wire_squares=[]
                touched_nodes=set()
                queue=[(r,c)]
                visited_black_squares.add((r,c))
                grid[r][c].color=yellow
                draw_callback()
                while queue:
                    pygame.event.pump()
                    curr_r,curr_c=queue.pop(0)
                    wire_squares.append((curr_r,curr_c))
                    for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nr,nc=curr_r+dr,curr_c+dc
                        if 0<=nr<rows and 0<=nc<rows:
                            neighbor=grid[nr][nc]
                            if neighbor.color==black and (nr,nc) not in visited_black_squares:
                                visited_black_squares.add((nr,nc))
                                queue.append((nr,nc))
                                neighbor.color=yellow
                                draw_callback()
                            elif neighbor in target_nodes:
                                touched_nodes.add(neighbor)
                for wr,wc in wire_squares: grid[wr][wc].color=black
                draw_callback()
                wire_length=len(wire_squares)
                touched_list=list(touched_nodes)
                for i in range(len(touched_list)):
                    for j in range(i+1,len(touched_list)):
                        n1=touched_list[i]
                        n2=touched_list[j]
                        if id(n1)>id(n2): n1,n2=n2,n1
                        pair=(n1,n2)
                        if pair not in graph_data: graph_data[pair]=[]
                        graph_data[pair].append(wire_length)
    return graph_data
def get_dev_matrix(graph_data,target_nodes):
    n=len(target_nodes)
    node_to_idx={node:i for i,node in enumerate(target_nodes)}
    matrix=[[[] for _ in range(n)] for _ in range(n)]
    for (n1,n2),distances in graph_data.items():
        idx1,idx2=node_to_idx[n1],node_to_idx[n2]
        matrix[idx1][idx2].extend(distances)
        matrix[idx2][idx1].extend(distances)
    print("\n==dev matrix==")
    for i,row in enumerate(matrix): print(f"node {i}: {row}")
    print("==============\n")
    return matrix,node_to_idx
def terminal_bfs(matrix,start=0):
    n=len(matrix)
    visited=[False]*n
    queue=[start]
    visited[start]=True
    traversal=[]
    while queue:
        u=queue.pop(0)
        traversal.append(u)
        for v in range(n):
            if matrix[u][v] and not visited[v]:
                visited[v]=True
                queue.append(v)
    print(f"[bfs] path: {traversal}")
def terminal_dfs(matrix,start=0):
    n=len(matrix)
    visited=[False]*n
    traversal=[]
    def dfs_util(u):
        visited[u]=True
        traversal.append(u)
        for v in range(n):
            if matrix[u][v] and not visited[v]: dfs_util(v)
    dfs_util(start)
    print(f"[dfs] path: {traversal}")
def terminal_dijkstra(matrix,start=0):
    n=len(matrix)
    dist=[float('inf')]*n
    dist[start]=0
    visited=[False]*n
    for _ in range(n):
        min_d=float('inf')
        u=-1
        for i in range(n):
            if not visited[i] and dist[i]<min_d:
                min_d=dist[i]
                u=i
        if u==-1: break
        visited[u]=True
        for v in range(n):
            if matrix[u][v]:
                weight=min(matrix[u][v])
                if not visited[v] and dist[u]+weight<dist[v]:
                    dist[v]=dist[u]+weight
    print(f"[dijkstra] dists: {dist}")
def terminal_bellman_ford(matrix,start=0):
    n=len(matrix)
    dist=[float('inf')]*n
    dist[start]=0
    edges=[]
    for u in range(n):
        for v in range(n):
            if matrix[u][v]: edges.append((u,v,min(matrix[u][v])))
    for _ in range(n-1):
        for u,v,w in edges:
            if dist[u]!=float('inf') and dist[u]+w<dist[v]: dist[v]=dist[u]+w
    print(f"[bellman-ford] dists: {dist}")
def modify_graph_keep_shortest(graph_data):
    new_graph_data={}
    for pair,distances in graph_data.items():
        new_graph_data[pair]=[min(distances)]
    return new_graph_data
def main():
    pygame.init()
    grid=initialize_grid()
    target_nodes=[]
    graph_data={}
    mode="grid"
    run=True
    while run:
        render_screen(win,grid,mode,graph_data,target_nodes)
        for event in pygame.event.get():
            if event.type==pygame.QUIT: run=False
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_g: mode="graph" if mode=="grid" else "grid"
                if event.key==pygame.K_c:
                    grid=initialize_grid()
                    target_nodes=[]
                    graph_data={}
                    mode="grid"
                if event.key==pygame.K_SPACE and mode=="grid":
                    graph_data=execute_path_search(grid,target_nodes,mode)
                if event.key==pygame.K_d:
                    if graph_data:
                        dev_matrix,mapping=get_dev_matrix(graph_data,target_nodes)
                        terminal_bfs(dev_matrix,0)
                        terminal_dfs(dev_matrix,0)
                        terminal_dijkstra(dev_matrix,0)
                        terminal_bellman_ford(dev_matrix,0)
                if event.key==pygame.K_f and mode=="graph":
                    if graph_data:
                        graph_data=modify_graph_keep_shortest(graph_data)
                        print("\n[graph filtered]")
                        get_dev_matrix(graph_data,target_nodes)
        if mode=="grid": handle_mouse_clicks(grid,target_nodes)
    pygame.quit()
if __name__=="__main__":
    main()
