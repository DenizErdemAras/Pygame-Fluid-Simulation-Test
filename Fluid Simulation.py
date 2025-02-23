import math
import pygame
import random

pygame.init()
WIDTH = 1600
HEIGHT = 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fluid Simulation")

clock = pygame.time.Clock()
FPS = 300

SIM_WIDTH = 900
SIM_HEIGHT = 600

BOX_SMOOTHING = 0.1
sim_x = (WIDTH - SIM_WIDTH)/2
sim_y = (HEIGHT - SIM_HEIGHT)/2
sim_xr = sim_x
sim_yr = sim_y

PARTICLE_AMOUNT = 800
# SIZE = 6 FAV
PARTICLE_SIZE = 7
POINT_SIZE = PARTICLE_SIZE * 0.7

cell_size = 2 * PARTICLE_SIZE

push_radius = cell_size
push_power = 1.5

pull_radius = 5* cell_size
pull_power = 0.0005

# viscosity = 0.5
#viscosity = (8-PARTICLE_SIZE)*0.1 + 0.05
viscosity = max(0.9-(PARTICLE_SIZE/7.5), 0.1)
#viscosity = 0.1

#vorticity = 0.3
#vorticity = (PARTICLE_SIZE-8)*0.06 + 0.6
vorticity = min(math.log(PARTICLE_SIZE,10),0.7)
#vorticity = 0.6

DAMPING = -0.0002

GRAVITY = 0.05

MOUSE_FORCE = 0.5

grid_width = math.ceil(SIM_WIDTH / cell_size)
grid_height = math.ceil(SIM_HEIGHT / cell_size)

grid = [[[] for _ in range(int(grid_height)+1)] for _ in range(int(grid_width)+1)]


def draw_point(x, y, radius, color):
    pygame.draw.circle(screen, color, (x, y), radius)


class Particle:
    def __init__(self, x, y, vx, vy, id):
        self.id = id
        self.x = x  # Position X
        self.y = y  # Position Y
        self.vx = vx  # Velocity X
        self.vy = vy  # Velocity Y
        self.gx = math.floor(x//cell_size)  # Grid X
        self.gy = math.floor(y//cell_size)  # Grid Y

    @property
    def position(self):
        return (self.x, self.y)

    @property
    def velocity(self):
        return (self.vx, self.vy)

    def accelerate(self, ax, ay):
        self.vx += ax
        self.vy += ay

    def move(self):
        self.vx = self.vx * (1 - DAMPING)
        self.vy = self.vy * (1 - DAMPING)

        self.x += self.vx
        self.y += self.vy

        if self.x > SIM_WIDTH:
            self.x = SIM_WIDTH-1
            self.vx = -self.vx * 0.3

        if self.y > SIM_HEIGHT:
            self.y = SIM_HEIGHT-1
            self.vy = -self.vy * 0.3

        if self.x < 0:
            self.x = 1
            self.vx = -self.vx * 0.3

        if self.y < 0:
            self.y = 1
            self.vy = -self.vy * 0.3

        newgx = math.floor(self.x//cell_size)
        newgy = math.floor(self.y//cell_size)

        if newgx != self.gx or newgy != self.gy:
            grid[self.gx][self.gy].remove(self.id)
            grid[newgx][newgy].append(self.id)
            self.gx = newgx
            self.gy = newgy

    def move_sim(self, x, y):
        self.x -= x
        self.y -= y

        if self.x > SIM_WIDTH:
            self.vx = SIM_WIDTH - self.x
            self.x = SIM_WIDTH-1

        if self.y > SIM_HEIGHT:
            self.vy = SIM_HEIGHT - self.y
            self.y = SIM_HEIGHT-1

        if self.x < 0:
            self.vx = -self.x
            self.x = 1

        if self.y < 0:
            self.vy = -self.y
            self.y = 1

    def draw(self):
        # draw_point(self.x + sim_x, self.y + sim_y, POINT_SIZE, (self.gx * math.floor(255/grid_width), self.gy * math.floor(255/grid_height), 255))
        # if self.id == 0:
        #     draw_point(self.x + sim_x, self.y + sim_y, POINT_SIZE,(self.gx * math.floor(255 / grid_width), self.gy * math.floor(255 / grid_height), 30))

        speed = math.dist((self.vx, self.vy), (0,0))

        color = pygame.Color(0)  # Create empty color
        color.hsva = (max((300 - (speed * 30)),0) % 360, 100, min(speed * 15 + 15, 100), 100)

        draw_point(self.x + sim_x, self.y + sim_y, POINT_SIZE, color)

class Simulation:
    def __init__(self, pos1, pos2, amount, cell_size):
        self.cell_size = cell_size
        self.particles = [Particle(random.randint(pos1[0], pos2[0]-1), random.randint(pos1[1], pos2[1]-1), 0, 0, i) for i in range(amount)]
        for i in range(len(self.particles)):
            grid[self.particles[i].gx][self.particles[i].gy].append(i)

    def tick(self):
        for p in self.particles:
            neighbors = []
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if p.gx + i >= 0 and p.gx + i < len(grid) and p.gy + j >= 0 and p.gy + j < len(grid[0]):
                        for neighbor in grid[p.gx + i][p.gy + j]:
                            neighbors.append(neighbor)

            total_force_x = 0
            total_force_y = 0

            force_pos_x = p.x
            force_pos_y = p.y

            viscosity_force_x = 0
            viscosity_force_y = 0
            viscosity_counter = 0

            for n in neighbors:
                dist = math.dist((force_pos_x, force_pos_y), self.particles[n].position)

                if dist < pull_radius:
                    closeness = 1-(dist/pull_radius)
                    viscosity_counter += closeness
                    viscosity_force_x += self.particles[n].vx * closeness
                    viscosity_force_y += self.particles[n].vy * closeness

                if dist < push_radius and dist != 0.0:
                    dist_x = force_pos_x - self.particles[n].x
                    dist_y = force_pos_y - self.particles[n].y

                    # multiplier = math.pow(-math.fabs(dist / push_radius) + 1,1) * push_power
                    multiplier = (1 - math.fabs(math.pow(dist / push_radius,3))) * push_power

                    force_x = (dist_x * multiplier) / dist
                    force_y = (dist_y * multiplier) / dist

                    total_force_x += force_x
                    total_force_y += force_y

                elif dist < pull_radius and dist != 0.0:

                    dist_x = force_pos_x - self.particles[n].x
                    dist_y = force_pos_y - self.particles[n].y

                    multiplier = (1 - ((math.pow(math.fabs(dist)-pull_radius,2))/pull_radius)) * pull_power

                    force_x = (dist_x * multiplier) / dist
                    force_y = (dist_y * multiplier) / dist

                    total_force_x += force_x
                    total_force_y += force_y

                    # p.vy = p.vy * (1-viscosity) + self.particles[n].vy * viscosity
                    # p.vx = p.vx * (1-viscosity) + self.particles[n].vx * viscosity

            if viscosity_counter > 0:
                # p.vx = p.vx * (1 - viscosity) + (viscosity_force_x/viscosity_counter) * viscosity
                # p.vy = p.vy * (1 - viscosity) + (viscosity_force_y/viscosity_counter) * viscosity

                w_vx = p.vx * (1 - viscosity) + (viscosity_force_x/viscosity_counter) * viscosity
                w_vy = p.vy * (1 - viscosity) + (viscosity_force_y/viscosity_counter) * viscosity

                w_v = math.dist((w_vx,w_vy), (0, 0))
                p_v = math.dist(p.velocity, (0,0))

                if w_v !=0:
                    p.vx =  (w_vx * (p_v / w_v)) * (vorticity) + (w_vx * (1-vorticity))
                    p.vy = (w_vy * (p_v / w_v)) * (vorticity) + (w_vy * (1-vorticity))

            p.accelerate(total_force_x, total_force_y)
            p.accelerate(0, GRAVITY)


            mouse_x, mouse_y = pygame.mouse.get_pos()

            dist = math.dist((force_pos_x, force_pos_y), (mouse_x - sim_x,mouse_y - sim_y))
            if dist < 100 and dist != 0.0:
                dist_x = force_pos_x - mouse_x + sim_x
                dist_y = force_pos_y - mouse_y + sim_y

                multiplier = math.pow(-math.fabs(dist / 100) + 1, 3) * 100
                multiplier = mouse_f

                force_x = (dist_x * multiplier) / dist
                force_y = (dist_y * multiplier) / dist

                p.accelerate(force_x, force_y)

        for p in self.particles:
            p.move_sim(sim_delta[0], sim_delta[1])
            p.move()

    def draw(self):
        for particle in self.particles:
            particle.draw()


sim = Simulation((0,0), (SIM_WIDTH, SIM_HEIGHT), PARTICLE_AMOUNT, cell_size)

last_position = None  # To store the last mouse position
mouse_delta = (0, 0)
sim_detla = (0, 0)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_position = pygame.mouse.get_pos()

    # If the left mouse button is held down
    if pygame.mouse.get_pressed()[0]:
        if last_position:
            # Calculate the change in position
            mouse_delta = ((current_position[0] - last_position[0]), (current_position[1] - last_position[1]))
        last_position = current_position

        sim_xr += mouse_delta[0]
        sim_yr += mouse_delta[1]
    else:
        # Reset the last position when the left button is released
        last_position = None
        mouse_delta = (0,0)
        
    if pygame.mouse.get_pressed()[2]:
        mouse_f = -0.8 * MOUSE_FORCE
    else:
        mouse_f = 1 * MOUSE_FORCE

    sim_oldx = sim_x
    sim_oldy = sim_y

    sim_x = sim_x * (1 - BOX_SMOOTHING) + sim_xr * BOX_SMOOTHING
    sim_y = sim_y * (1 - BOX_SMOOTHING) + sim_yr * BOX_SMOOTHING

    sim_delta = (sim_x - sim_oldx), (sim_y - sim_oldy)

    screen.fill((0, 0, 0))


    draw_point(current_position[0], current_position[1], 100, (0, 5, 10))
    draw_point(current_position[0], current_position[1], 80, (5, 12, 20))
    draw_point(current_position[0], current_position[1], 55, (10, 18, 30))
    draw_point(current_position[0], current_position[1], 25, (13, 20, 30))
    pygame.draw.rect(screen, (50, 50, 50), pygame.Rect(sim_xr-(POINT_SIZE+1), sim_yr-(POINT_SIZE+1), SIM_WIDTH+(2*(POINT_SIZE+1)), SIM_HEIGHT+(2*(POINT_SIZE+1))), 1, 0)
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(sim_x-(POINT_SIZE+1), sim_y-(POINT_SIZE+1), SIM_WIDTH+(2*(POINT_SIZE+1)), SIM_HEIGHT+(2*(POINT_SIZE+1))), 1, 0)

    sim.tick()
    sim.draw()


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()