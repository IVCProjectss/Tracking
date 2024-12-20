import pygame
import cv2
from pygame.locals import *
from tracking import ObjectTracking  # Import ObjectTracking class

# Initialize object tracker
tracker = ObjectTracking()

# Initialize the camera
cam = tracker.initialize_camera()

# Initialize Pygame
pygame.init()

# Screen settings
screen_width, screen_height = 600, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Breakout')

# Color settings
bg = (234, 218, 184)
paddle_outline = (100, 100, 100)
paddle_green = (86, 174, 87)
text_col = (78, 81, 139)
block_red = (242, 85, 96)
block_blue = (69, 177, 232)
font = pygame.font.SysFont('Constantia', 30)
clock = pygame.time.Clock()
fps = 30
live_ball = False
cols = 6
rows = 6
game_over = 0

# Draw text function
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Wall class
class Wall:
    def __init__(self):
        self.width = screen_width // cols
        self.height = 50

    def create_wall(self):
        self.blocks = []
        for row in range(rows):
            block_row = []
            for col in range(cols):
                block_x = col * self.width
                block_y = row * self.height
                rect = pygame.Rect(block_x, block_y, self.width, self.height)
                strength = 3 if row < 2 else 2 if row < 4 else 1
                block_row.append([rect, strength])
            self.blocks.append(block_row)

    def draw_wall(self):
        for row in self.blocks:
            for block in row:
                block_col = block_blue if block[1] == 3 else block_red
                pygame.draw.rect(screen, block_col, block[0])
                pygame.draw.rect(screen, bg, block[0], 2)

# Paddle class
class Paddle:
    def __init__(self):
        self.width = screen_width // cols
        self.height = 20
        self.color = paddle_green
        self.reset()

    def move_to(self, x):
        self.rect.x = max(0, min(screen_width - self.width, x - self.width // 2))

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, paddle_outline, self.rect, 3)

    def reset(self):
        self.x = (screen_width // 2) - (self.width // 2)
        self.y = screen_height - (self.height * 2)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

# GameBall class
class GameBall:
    def __init__(self, x, y):
        self.ball_rad = 10
        self.reset(x, y)

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Collisions with walls (left and right)
        if self.rect.left < 0 or self.rect.right > screen_width:
            self.speed_x *= -1
        # Collision with top
        if self.rect.top < 0:
            self.speed_y *= -1
        # Collision with bottom (game over)
        if self.rect.bottom > screen_height:
            return -1  # Game over

        # Collision with paddle
        if self.rect.colliderect(paddle.rect):
            if abs(self.rect.bottom - paddle.rect.top) < 5 and self.speed_y > 0:
                self.speed_y *= -1

        # Collision with blocks (check each block in the wall)
        for row in wall.blocks:
            for block in row:
                if self.rect.colliderect(block[0]):
                    # Destroy block by reducing its strength
                    self.speed_y *= -1
                    block[1] -= 1
                    if block[1] <= 0:
                        row.remove(block)
        return 0

    def draw(self):
        pygame.draw.circle(screen, paddle_green, (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad), self.ball_rad)
        pygame.draw.circle(screen, paddle_outline, (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad), self.ball_rad, 3)

    def reset(self, x, y):
        self.rect = pygame.Rect(x - self.ball_rad, y, self.ball_rad * 2, self.ball_rad * 2)
        self.speed_x = 4
        self.speed_y = -4

# Game objects
wall = Wall()
wall.create_wall()
paddle = Paddle()
ball = GameBall(paddle.x + (paddle.width // 2), paddle.y - paddle.height)

# Main game loop
run = True
while run:
    clock.tick(fps)
    screen.fill(bg)

    # Camera processing
    ret, frame = cam.read()
    if not ret:
        break

    if tracker.roi_selected:
        # Track object position using CamShift and get the new position
        annotated_frame, x_center = tracker.track_object(frame)
        if x_center is not None:
            # Move paddle based on tracked position
            paddle.move_to(x_center)
    else:
        cv2.putText(frame, "Press 'r' to select ROI", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Display the annotated frame with object detection
    cv2.imshow("Camera Feed with Object Tracking", frame)

    # Draw game objects
    wall.draw_wall()
    paddle.draw()
    ball.draw()

    # Ball
    if live_ball:
        game_over = ball.move()
        if game_over:
            live_ball = False
    else:
        draw_text("CLICAR PARA COMEÇAR", font, text_col, 140, screen_height // 2 + 80)
        ball.reset(paddle.x + (paddle.width // 2), paddle.y - paddle.height)

    for event in pygame.event.get():
        if event.type == QUIT:
            run = False
        if event.type == MOUSEBUTTONDOWN and not live_ball:
            live_ball = True

    # Wait for user input
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        run = False
    if key == ord('r'):
        tracker.roi_selected = False
        print("Select a new ROI.")
        tracker.initialize_tracking(frame)

    pygame.display.update()

# Release resources
cam.release()
cv2.destroyAllWindows()
pygame.quit()
