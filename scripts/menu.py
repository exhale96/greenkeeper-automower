import pygame
import sys
from motor_driver import MotorDriver, launch_rtk_loop, cleanup
import numpy as np
import cv2
import time
from camera_manager import CameraManager
from computer_vision import process_frame, process_frame_with_midas, init_vision
import subprocess
import atexit
import threading
from mapper import LawnMowerMapping

camera_manager = CameraManager()
# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GreenKeeper Menu")
WHITE = (255, 255, 255)
GREEN1 = (33,78,52)
PINK = 	(239,208,202)
GREEN2 = (92,116,87)
YELLOW = (247,246,54)
DARK = (28,30,38)
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
    def __init__(self, text, x, y, width, height, color, text_color=GREEN1):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        # Draw button
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, DARK, self.rect, 2)
        # Draw text
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        return self.is_hovered(mouse_pos) and mouse_click

# Create buttons for the menu
button_rc = Button("RC Mode", 200, 100, 240, 50, PINK)
button_mapping = Button("Mapping", 200, 170, 240, 50, PINK)
button_sentry = Button("Sentry Mode", 200, 240, 240, 50, PINK)
button_pathing = Button("Pathing Mode", 200, 310, 240, 50, PINK)
button_quit = Button("QUIT", 400, 590, 240, 50, (255, 0, 0), YELLOW) 
button_increase_speed = Button("+", 70, 490, 40, 40, PINK)  # Increase button
button_decrease_speed = Button("-", 30, 490, 40, 40, PINK) # 
button_currently_mapping = Button("Currently Mapping", 200, 240, 290, 50, PINK)
button_back = Button("<- Esc", 0, 0, 100, 50, YELLOW, GREEN1)

def draw_menu_screen():
    screen.fill(GREEN1)  # Fill the background with (COLOR)


    # Draw buttons
    button_rc.draw(screen)
    button_mapping.draw(screen)
    button_sentry.draw(screen)
    button_pathing.draw(screen)
    button_quit.draw(screen)

    # Update the display
    pygame.display.flip()

def sentry_mode():

    print("Sentry Mode activated!")

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    camera_manager.stop_camera()  # Close the camera
                    return STATE_MENU  # Go back to main menu

        # Process Frame with CV
        annotated_frame, fps = process_frame_with_midas(camera_manager.picam2)
        fps = fps/2
        frame_rotated = np.rot90(annotated_frame, k=-1)
        frame_flipped = cv2.flip(frame_rotated, 1)
        frame_surface = pygame.surfarray.make_surface(frame_flipped)
        screen.blit(frame_surface, (0, 0))

        ## Display FPS in PyGame ##
        font = pygame.font.Font(None, 36)
        fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        pygame.display.flip()

    # Cleanup
    camera_manager.stop_camera()

def pathing_mode():

    ## Setup ##
    screen.fill(GREEN1)  # Clears the screen with the background color

    ## Main Loop ##
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Exit the pathing mode and return to the menu
        

        # Draw or update any display related to pathing mode here
        button_quit.draw(screen)

        pygame.display.flip()
        pygame.time.delay(50)  # To avoid consuming too many resources

    return STATE_MENU
def mapping_mode():

    ## Setup ##
    screen.fill(GREEN1)  # Clears the screen with the background color
    rtk_thread = threading.Thread(target=launch_rtk_loop, daemon=True)
    rtk_thread.start()
    motor_driver = MotorDriver()
    speed = 0.6

    ## Main Loop ##
    running = True
    while running:

        ## Keys & Inputs ##
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    print("Up Arrow Pressed: Move Forward")
                    MotorDriver.set_motor(speed, speed)
                elif event.key == pygame.K_DOWN:
                    print("Down Arrow Pressed: Move Backward")
                    MotorDriver.set_motor(-speed, -speed)
                elif event.key == pygame.K_LEFT:
                    print("Left Arrow Pressed: Turn Left")
                    MotorDriver.set_motor(-speed, speed)
                elif event.key == pygame.K_RIGHT:
                    print("Right Arrow Pressed: Turn Right")
                    MotorDriver.set_motor(speed, -speed)
                elif event.key == pygame.K_0:
                    print("0 pressed: Activating Blade Motor")
                    MotorDriver.set_blade(0.3)
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    print("Key Released: Stop Motors")
                    motor_driver.stop_motors()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_increase_speed.is_clicked(mouse_pos, True):
                    speed = min(speed + 0.1, 1.0)
                    print("Speed Increased!")
                elif button_decrease_speed.is_clicked(mouse_pos, True):
                    speed = max(speed - 0.1, 0.1)
                    print("Speed Decreased!")
        
        ## Update GUI ##
        button_currently_mapping.draw(screen)

        ## Update Display (last) ##
        pygame.display.flip()
    ## Exit Process ##                 
    cleanup()
    atexit.register(cleanup)
    return STATE_MENU
    
def rc_mode():
    ## Function Setup ##
    motor_driver = MotorDriver()
    speed = 0.3
    controls_font = pygame.font.Font(None, 28)
    control_panel_width = 210# Width of the control panel
    control_panel_height = 180# Height of the control panel
    control_panel_surface = pygame.Surface((control_panel_width, control_panel_height))
    control_panel_surface.set_alpha(150)  # Set transparency (0-255, where 255 is fully opaque)
    control_panel_surface.fill((0, 0, 0))  # Fill with black color

    running = True
    while running:

        ## Keys & Inputs ##
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    print("Up Arrow Pressed: Move Forward")
                    print(speed)
                    motor_driver.set_motor(-speed, -speed)
                elif event.key == pygame.K_DOWN:
                    print("Down Arrow Pressed: Move Backward")
                    motor_driver.set_motor(speed, speed)
                elif event.key == pygame.K_LEFT:
                    print("Left Arrow Pressed: Turn Left")
                    motor_driver.set_motor(-speed, speed)
                elif event.key == pygame.K_RIGHT:
                    print("Right Arrow Pressed: Turn Right")
                    motor_driver.set_motor(speed, -speed)
                elif event.key == pygame.K_0:
                    print("0 pressed: Activating Blade Motor")
                    motor_driver.set_blade(0.2)
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_0]:
                    print("Key Released: Stop Motors")
                    motor_driver.stop_motors()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_increase_speed.is_clicked(mouse_pos, True):
                    speed = min(speed + 0.1, 1.0)
                    print("Speed Increased!")
                elif button_decrease_speed.is_clicked(mouse_pos, True):
                    speed = max(speed - 0.1, 0.1)
                    print("Speed Decreased!")

        ## Get & Update Camera Frames ##
        frame = camera_manager.picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        resized_frame = cv2.resize(frame_bgr, (640, 640))
        frame_surface = pygame.surfarray.make_surface(np.transpose(resized_frame, (1, 0, 2)))
        screen.blit(frame_surface, (0, 0))
        

        ## Draw GUI ##
        screen.blit(control_panel_surface, (20, 530))  # Position of the control panel
        controls_text = [
            "Speed: " + str(round(speed*100,1))+ "%",
            "Controls: Arrow Keys",
            "Blade Act.: '0' Key",
        ]
        button_decrease_speed.draw(screen)
        button_increase_speed.draw(screen)
        button_back.draw(screen)

        y_offset = 10  # Starting offset for text drawing (within the background)
        for line in controls_text:
            control_line = controls_font.render(line, True, (255, 255, 255))
            screen.blit(control_line, (30, 540 + y_offset))  # Adjust position within the panel
            y_offset += 30  # Move down for the next line
        
        ## Update Display (last) ##
        pygame.display.flip()
    camera_manager.stop_camera()
    return STATE_MENU

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
            init_vision()
            camera_manager.init_camera()
            return STATE_RC
        
        elif button_mapping.is_clicked(mouse_pos, mouse_click):
            print("Mapping Selected")
            return STATE_MAPPING

        elif button_sentry.is_clicked(mouse_pos, mouse_click):
            print("Sentry Mode Selected")
            init_vision()
            camera_manager.init_camera()
            return STATE_SENTRY


        elif button_pathing.is_clicked(mouse_pos, mouse_click):
            print("Pathing Mode Selected")
            return STATE_PATHING

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
