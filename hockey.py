import pygame
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60

# Colors (R, G, B, A)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 51, 153)  # Leafs Blue
LEAFS_BLUE = (0, 51, 153)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128, 128)
ICE_BLUE = (220, 240, 255)
PUCK_SHADOW = (100, 100, 100, 70)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hockey Shooting Game - Maple Leafs Edition")

# Load and scale Leafs logo (only for goalie)
LOGO_SIZE = 40
try:
    leafs_logo = pygame.image.load('leafs_logo.png')
    leafs_logo = pygame.transform.scale(leafs_logo, (LOGO_SIZE, LOGO_SIZE))
except:
    # Create a simple leaf shape if image not found
    leafs_logo = pygame.Surface((LOGO_SIZE, LOGO_SIZE), pygame.SRCALPHA)
    pygame.draw.polygon(leafs_logo, LEAFS_BLUE, [
        (20, 0), (35, 15), (30, 30), (20, 35),
        (10, 30), (5, 15), (20, 0)
    ])

class Net:
    def __init__(self):
        self.width = 300
        self.height = 200
        self.depth = 50
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT // 2 - self.height // 2 - 50

    def draw(self, screen):
        # Draw ice reflection
        pygame.draw.polygon(screen, ICE_BLUE, [
            (self.x - 20, self.y + self.height),
            (self.x + self.width + 20, self.y + self.height),
            (WIDTH//2 + 200, HEIGHT),
            (WIDTH//2 - 200, HEIGHT)
        ])
        
        # Draw main frame
        pygame.draw.rect(screen, RED, (self.x - 4, self.y, 8, self.height), 0)
        pygame.draw.rect(screen, RED, (self.x + self.width - 4, self.y, 8, self.height), 0)
        pygame.draw.rect(screen, RED, (self.x, self.y - 4, self.width, 8), 0)
        
        # Draw depth posts
        pygame.draw.line(screen, RED, (self.x, self.y), 
                        (self.x - self.depth, self.y + self.depth), 4)
        pygame.draw.line(screen, RED, (self.x + self.width, self.y), 
                        (self.x + self.width + self.depth, self.y + self.depth), 4)
        pygame.draw.line(screen, RED, (self.x, self.y + self.height), 
                        (self.x - self.depth, self.y + self.height + self.depth), 4)
        pygame.draw.line(screen, RED, (self.x + self.width, self.y + self.height), 
                        (self.x + self.width + self.depth, self.y + self.height + self.depth), 4)
        
        # Draw mesh
        mesh_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in range(self.x + 15, self.x + self.width, 15):
            pygame.draw.line(mesh_surface, GRAY, (x, self.y), (x, self.y + self.height))
            pygame.draw.line(mesh_surface, GRAY, (x, self.y), 
                           (x + self.depth//2, self.y + self.depth))
        
        for y in range(self.y + 15, self.y + self.height, 15):
            pygame.draw.line(mesh_surface, GRAY, (self.x, y), (self.x + self.width, y))
            pygame.draw.line(mesh_surface, GRAY, (self.x, y), 
                           (self.x - self.depth//2, y + self.depth))
        
        screen.blit(mesh_surface, (0, 0))

    def check_goal(self, puck):
        return (puck.x > self.x and 
                puck.x < self.x + self.width and 
                puck.y > self.y and 
                puck.y < self.y + self.height and 
                puck.z > 300)

class Goalie:
    def __init__(self, net):
        self.width = 80
        self.height = 140
        self.head_size = 30
        self.net = net
        self.y = net.y + net.height - self.height
        self.x = net.x + (net.width // 2) - (self.width // 2)
        self.speed = 3
        self.direction = 1
        self.block_time = 0

    def move(self):
        self.x += self.speed * self.direction
        if self.x + self.width > self.net.x + self.net.width - 20:
            self.direction = -1
        elif self.x < self.net.x + 20:
            self.direction = 1

    def draw(self, screen):
        # Draw body
        pygame.draw.rect(screen, LEAFS_BLUE, (self.x, self.y + self.head_size, 
                                            self.width, self.height - self.head_size))
        
        # Draw head
        pygame.draw.circle(screen, (255, 218, 185), 
                         (self.x + self.width//2, self.y + self.head_size//2), 
                         self.head_size//2)
        
        # Draw Leafs logo on jersey
        screen.blit(leafs_logo, (self.x + self.width//2 - LOGO_SIZE//2, 
                                self.y + self.head_size + 20))
        
        # Draw pads
        pygame.draw.rect(screen, WHITE, 
                        (self.x - 5, self.y + self.height - 30, 
                         self.width + 10, 30))

    def check_collision(self, puck):
        if puck.z > 200:
            return (puck.x > self.x and 
                    puck.x < self.x + self.width and 
                    puck.y > self.y and 
                    puck.y < self.y + self.height)
        return False

class Puck:
    def __init__(self):
        self.radius = 15
        self.reset()
        self.shadow_offset = 10
        self.reset_delay = 0
        self.gravity = 0.3
        self.velocity_decay = 0.98
        self.is_dragging = False

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.z = 0
        self.shot = False
        self.drag_start = None
        self.current_radius = self.radius
        self.rotation = 0
        self.spin_speed = 0
        self.height_offset = 0
        self.blocked = False
        self.scored = False
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.is_dragging = False
        self.initial_y = self.y

    def start_drag(self, pos):
        if not self.shot and math.dist((self.x, self.y), pos) < self.radius:
            self.drag_start = pos
            self.is_dragging = True
            return True
        return False

    def shoot(self, release_pos):
        if self.drag_start and self.is_dragging:
            if release_pos[1] > self.drag_start[1]:
                self.drag_start = None
                self.is_dragging = False
                return
            
            dx = self.drag_start[0] - release_pos[0]
            dy = self.drag_start[1] - release_pos[1]
            drag_distance = math.sqrt(dx*dx + dy*dy)
            
            self.shot = True
            self.shot_time = pygame.time.get_ticks()
            power = min(drag_distance * 0.1, 15)
            angle = math.atan2(dy, dx)
            
            # Set velocities for forward arc motion
            self.vx = -power * math.cos(angle) * 4
            self.vy = -power * math.sin(angle) * 4
            self.vz = power * 4
            
            self.spin_speed = power * 6
            self.initial_y = self.y
            
            self.drag_start = None
            self.is_dragging = False

    def move(self):
        if self.shot:
            if self.blocked or self.scored:
                current_time = pygame.time.get_ticks()
                if current_time - self.reset_delay >= 2000:
                    self.reset()
                return

            self.vy += self.gravity
            
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            
            self.vx *= self.velocity_decay
            self.vy *= self.velocity_decay
            self.vz *= self.velocity_decay
            
            self.rotation += self.spin_speed
            self.spin_speed *= 0.99
            
            depth_scale = max(0.2, 1 - (self.z / 800))
            self.current_radius = int(self.radius * depth_scale)
            
            self.height_offset = self.y - self.initial_y
            
            if (self.y > HEIGHT or self.z > 1000 or 
                self.x < 0 or self.x > WIDTH):
                self.reset()

    def draw(self, screen):
        if self.drag_start and self.is_dragging:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[1] < self.drag_start[1]:
                pygame.draw.line(screen, BLACK, self.drag_start, mouse_pos, 2)
                
                drag_distance = math.dist(self.drag_start, mouse_pos)
                power_percentage = min(drag_distance / 133, 1)
                power_color = (int(255 * power_percentage), 
                             int(255 * (1 - power_percentage)), 0)
                pygame.draw.circle(screen, power_color, mouse_pos, 5)

        # Draw shadow
        shadow_y_offset = max(0, self.height_offset / 3)
        pygame.draw.ellipse(screen, PUCK_SHADOW, 
                          (self.x - self.current_radius,
                           self.y + self.shadow_offset + shadow_y_offset,
                           self.current_radius * 2,
                           self.current_radius))

        # Draw puck
        pygame.draw.ellipse(screen, BLACK,
                          (self.x - self.current_radius,
                           self.y - self.current_radius - self.height_offset,
                           self.current_radius * 2,
                           self.current_radius * 2))
        
        # Draw highlight
        highlight_x = self.x + math.cos(math.radians(self.rotation)) * self.current_radius * 0.3
        highlight_y = self.y - self.height_offset + math.sin(math.radians(self.rotation)) * self.current_radius * 0.3
        pygame.draw.circle(screen, (50, 50, 50),
                         (int(highlight_x), int(highlight_y)),
                         self.current_radius // 4)

def main():
    clock = pygame.time.Clock()
    net = Net()
    goalie = Goalie(net)
    puck = Puck()
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                puck.start_drag(pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONUP:
                puck.shoot(pygame.mouse.get_pos())

        puck.move()
        goalie.move()

        if puck.shot and not puck.blocked and not puck.scored:
            if goalie.check_collision(puck):
                puck.blocked = True
                puck.reset_delay = pygame.time.get_ticks()
            elif net.check_goal(puck):
                score += 1
                puck.scored = True
                puck.reset_delay = pygame.time.get_ticks()

        screen.fill(WHITE)
        net.draw(screen)
        goalie.draw(screen)
        puck.draw(screen)

        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        if puck.blocked:
            blocked_font = pygame.font.Font(None, 48)
            blocked_text = blocked_font.render("Save!", True, LEAFS_BLUE)
            screen.blit(blocked_text, (WIDTH//2 - 60, HEIGHT//2))
        elif puck.scored:
            goal_font = pygame.font.Font(None, 48)
            goal_text = goal_font.render("Goal!", True, LEAFS_BLUE)
            screen.blit(goal_text, (WIDTH//2 - 40, HEIGHT//2))

        if not puck.shot and not puck.drag_start:
            instruction_text = font.render("Click and drag to shoot!", True, BLACK)
            screen.blit(instruction_text, (WIDTH//2 - 100, HEIGHT - 150))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
