import pygame
import sys
from motor_driver import MotorDriver
import numpy as np
import cv2
import subprocess
import time

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GreenKeeper Menu")

# Colors & Font
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
BLUE = (0, 0, 255)
font = pygame.font.Font(None, 48)

# States
STATE_MENU = "menu"
STATE_RC = "rc_mode"
STATE_MAPPING = "mapping"
STATE_SENTRY = "sentry"
STATE_PATHING = "pathing"
STATE_QUIT = "quit"
current_state = STATE_MENU


# Menu button class
class Button:
    def __init__(self, text, x, y, width, height, color, text_color=WHITE):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        # Draw button
        pygame.draw.rect(screen, self.color, self.rect)
        # Draw text
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        return self.is_hovered(mouse_pos) and mouse_click

# Create buttons for the menu
button_rc = Button("RC Mode", 200, 100, 240, 50, GRAY)
button_mapping = Button("Mapping", 200, 170, 240, 50, GRAY)
button_sentry = Button("Sentry Mode", 200, 240, 240, 50, GRAY)
button_pathing = Button("Pathing Mode", 200, 310, 240, 50, GRAY)
button_quit = Button("QUIT", 200, 380, 240, 50, (255, 0, 0)) 

# Game loop
def draw_menu_screen():
    screen.fill(WHITE)  # Fill the background with white
    screen.fill(WHITE)  # Fill the background with white

    # Draw buttons
    button_rc.draw(screen)
    button_mapping.draw(screen)
    button_sentry.draw(screen)
    button_pathing.draw(screen)
    button_quit.draw(screen)

    # Update the display
    pygame.display.flip()

def sentry_mode():
    print("Sentry Mode activated!")  # Placeholder
    pygame.time.wait(1000)
    cv2.destroyAllWindows()
    time.sleep(2)
    subprocess.run(["/home/green/venv/bin/python", "/home/green/Desktop/greenkeeper_project/motor_driver.py"])

def pathing_mode():
    print("Pathing Mode activated!")  # Placeholder
    pygame.time.wait(1000)

def mapping_mode():
    ...
    
def rc_mode():
    motor_driver = MotorDriver()  # Initialize the motor driver
    cap = cv2.VideoCapture(0)  # Open the camera

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Capture the frame from the camera
        ret, frame = cap.read()
        if not ret:
            continue

        # Process the frame for computer vision
        # Here you can add your computer vision processing code
        frame = cv2.flip(frame, 1)  # Example: flip the frame horizontally

        # Convert the frame to a Pygame surface
        frame_surface = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))

        # Display the frame
        screen.blit(frame_surface, (0, 0))

        # Motor control logic here
        # For example, using arrow keys to control motors
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            motor_driver.set_motor(1, 1)
        elif keys[pygame.K_DOWN]:
            motor_driver.set_motor(-1, -1)
        elif keys[pygame.K_LEFT]:
            motor_driver.set_motor(-1, 1)
        elif keys[pygame.K_RIGHT]:
            motor_driver.set_motor(1, -1)
        else:
            motor_driver.stop_motors()

        pygame.display.flip()

    cap.release()
    pygame.quit()
    sys.exit()


# Menu function to transition to RC mode
def run_menu():

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Mouse events
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        # Check button interactions
        if button_rc.is_clicked(mouse_pos, mouse_click):
            print("RC Mode Selected")
            running = False  # Stop the menu loop and go to RC mode
            rc_mode()  # Call RC mode function

        elif button_mapping.is_clicked(mouse_pos, mouse_click):
            print("Idle Mode Selected")
            pygame.time.wait(1000)  # Just a placeholder
            mapping_mode()

        elif button_sentry.is_clicked(mouse_pos, mouse_click):
            sentry_mode()


        elif button_pathing.is_clicked(mouse_pos, mouse_click):
            pathing_mode()

        elif button_quit.is_clicked(mouse_pos, mouse_click):
            print("Exiting...")
            running = False

        # Draw the menu
        draw_menu_screen()
        pygame.time.delay(50)

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    while current_state != STATE_QUIT:
        if current_state == STATE_MENU:
            current_state = run_menu()

        elif current_state == STATE_RC:
            current_state = rc_mode()

        elif current_state == STATE_MAPPING:
            current_state = mapping_mode()

        elif current_state == STATE_SENTRY:
            current_state = sentry_mode()

        elif current_state == STATE_PATHING:
            current_state = pathing_mode()
    run_menu()
