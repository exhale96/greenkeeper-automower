import pygame
import sys
from motor_driver import MotorDriver
import numpy as np
import cv2
import time
from camera_manager import CameraManager
from computer_vision import process_frame, process_frame_with_midas, init_vision
import subprocess
import atexit
import threading
from mapper import LawnMowerMapping
import os


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
STATE_WRITE_NEW_MAP = "write_new_map"

current_state = STATE_MENU

# Menu button class
class Button:
    def __init__(self, text, x, y, width=None, height=None, color=PINK, text_color=GREEN1, padding_x=20, padding_y=10):
        self.text = text
        self.color = color
        self.text_color = text_color
        self.padding_x = padding_x
        self.padding_y = padding_y

        # Render the text to measure size
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect()

        # Auto-size button if width/height not given
        self.width = width if width else text_rect.width + 2 * padding_x
        self.height = height if height else text_rect.height + 2 * padding_y
        self.rect = pygame.Rect(x, y, self.width, self.height)

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
button_sentry = Button("Sentry Mode", 200, 170, 240, 50, PINK)
button_mapping = Button("Create a new map", 165, 240, 310, 50, PINK)
button_pathing = Button("Choose a map", 200, 310, 240, 50, PINK)
button_quit = Button("QUIT", 400, 590, 240, 50, (255, 0, 0), YELLOW) 
button_delete_map = Button("Cancel & Delete", 170, 170, 350, 50, (255,0,0), YELLOW)
button_save_map = Button("Stop & Save", 200, 240, 240, 50, GREEN2, YELLOW)
button_enter_mapname = Button("Click here to enter map name: ",200, 240, 290, 50, PINK)
button_increase_speed = Button("+", 70, 490, 40, 40, PINK)  # Increase button
button_decrease_speed = Button("-", 30, 490, 40, 40, PINK) # 
button_back = Button("<- Esc", 0, 0, 100, 50, YELLOW, GREEN1)




def launch_rtk_loop():
    global rtk_process
    email = "irc16@scarletmail.rutgers.edu"
    print("Launching RTK process...")
    rtk_process = subprocess.Popen([
        "python", "rtk_coords.py", 
        "-u", email, 
        "-p", "none", 
        "rtk2go.com", 
        "2101", 
        "NJ_north_central"
    ])
    return_code = rtk_process.wait()
    print(f"RTK process exited with code: {return_code}")

def cleanup():
    print("Cleaning up... Terminating RTK process (if running).")
    try:
        if rtk_process.poll() is None:
            rtk_process.terminate()
            rtk_process.wait(timeout=5)
            print("RTK process cleaned.")
    except Exception as e:
        print(f"Could not terminate RTK process: {e}")

def get_map_dir():
    maps_dir = os.path.join("..","assets", "maps")
    return [f for f in os.listdir(maps_dir) if os.path.isfile(os.path.join(maps_dir, f))]

def choose_map(surface):
    pygame.event.clear()
    font = pygame.font.SysFont(None, 36)
    title_font = pygame.font.SysFont(None, 48)
    map_dir = "../assets/maps/"
    maps = [f for f in os.listdir(map_dir) if f.endswith(".txt")]

    item_height = 50
    padding = 10
    start_y = 100
    scroll_offset = 0
    max_display = 8  # number of items visible at once

    clock = pygame.time.Clock()
    done = False

    while not done:
        screen.fill((30, 30, 30))
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll up
                    scroll_offset = max(scroll_offset - 1, 0)
                elif event.button == 5:  # scroll down
                    scroll_offset = min(scroll_offset + 1, max(0, len(maps) - max_display))
                elif event.button == 1:  # left click
                    for i, name in enumerate(maps[scroll_offset:scroll_offset + max_display]):
                        rect = pygame.Rect(100, start_y + i * (item_height + padding), 400, item_height)
                        if rect.collidepoint(mouse_x, mouse_y):
                            return name  # return selected map
                elif button_back.is_clicked((mouse_x, mouse_y), True):
                    return None
            
        # Draw prompt
        title = title_font.render("Choose a Map:", True, (255, 255, 255))
        screen.blit(title, (100, 30))

        # Draw list
        for i, name in enumerate(maps[scroll_offset:scroll_offset + max_display]):
            y = start_y + i * (item_height + padding)
            rect = pygame.Rect(100, y, 400, item_height)
            hover = rect.collidepoint(mouse_x, mouse_y)

            pygame.draw.rect(screen, (70, 70, 70) if hover else (50, 50, 50), rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)
            text_surface = font.render(name, True, (255, 255, 255))
            screen.blit(text_surface, (rect.x + 10, rect.y + 10))

        button_back.draw(screen)

        pygame.display.flip()
        clock.tick(60)

def draw_menu_screen():
    pygame.event.clear()
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
    pygame.event.clear()
    control_panel_width = 100# Width of the control panel
    control_panel_height = 30# Height of the control panel
    control_panel_surface = pygame.Surface((control_panel_width, control_panel_height))
    control_panel_surface.set_alpha(150)  # Set transparency (0-255, where 255 is fully opaque)
    control_panel_surface.fill((0, 0, 0))  # Fill with black color

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
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_back.is_clicked(mouse_pos, True):
                    print("Returning to main menu")
                    running = False

        # Process Frame with CV
        annotated_frame, fps = process_frame_with_midas(camera_manager.picam2)
        fps = fps/2
        frame_rotated = np.rot90(annotated_frame, k=-1)
        frame_flipped = cv2.flip(frame_rotated, 1)
        frame_surface = pygame.surfarray.make_surface(frame_flipped)
        screen.blit(frame_surface, (0, 0))
        

        ## Display FPS in PyGame ##
        button_back.draw(screen)
        screen.blit(control_panel_surface, (550, 0))
        font = pygame.font.Font(None, 36)
        fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        screen.blit(fps_text, (550, 0))
      # Position of the control panel
        pygame.display.flip()

    # Cleanup
    camera_manager.stop_camera()

def pathing_mode():
    ## Setup ##
    pygame.event.clear()
    screen.fill(GREEN1)
    map_files = get_map_dir()
    scroll_offset = 0
    max_visible = 6
    selected_map = None
    map_buttons = []

    def update_map_buttons():
        map_buttons.clear()
        for i, map_name in enumerate(map_files[scroll_offset:scroll_offset + max_visible]):
            btn = Button(map_name, 200, 100 + i * 60, 240, 50, PINK)
            map_buttons.append((btn, map_name))

    update_map_buttons()

    running = True
    while running:
        screen.fill(GREEN1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return STATE_QUIT
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return STATE_MENU
                elif event.key == pygame.K_DOWN:
                    if scroll_offset + max_visible < len(map_files):
                        scroll_offset += 1
                        update_map_buttons()
                elif event.key == pygame.K_UP:
                    if scroll_offset > 0:
                        scroll_offset -= 1
                        update_map_buttons()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_back.is_clicked(mouse_pos, True):
                    #running = False
                    chosen_map = choose_map(screen)

                    if chosen_map != None:
                        print("map selected. Next step is to add the pathing logic here")
                    else:
                        print("No map selected. Returning to main menu.")
                        return STATE_MENU
                for btn, map_name in map_buttons:
                    if btn.is_clicked(mouse_pos, True):
                        selected_map = map_name
                        print(f"Selected map: {selected_map}")
                        # TODO: Load or pass the selected map to your pathing logic
                        return STATE_PATHING

        for btn, _ in map_buttons:
            btn.draw(screen)

        button_back.draw(screen)
        pygame.display.flip()
        pygame.time.delay(50)
    print("Returning to main menu...") 
    return STATE_MENU

def mapping_mode():
    
    def write_new_map():
        input_surface = pygame.Surface((WIDTH, HEIGHT))
        font = pygame.font.SysFont(None, 48)
        input_box = pygame.Rect(100, 200, 400, 50)
        color_inactive = pygame.Color('lightskyblue3')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        text = ''
        done = False

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # If the user clicked on the input_box rect.
                    if input_box.collidepoint(event.pos):
                        active = not active
                    else:
                        active = False
                    color = color_active if active else color_inactive
                    if button_back.is_clicked(event.pos, True):
                        done = True

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("DEBUG esc pressed")
                        done = True                 
                    if active:
                        if event.key == pygame.K_ESCAPE:
                            print("DEBUG esc pressed")
                            done = True
                        if event.key == pygame.K_RETURN:
                            done = True                        
                            open("../assets/maps/" + text.strip() + ".txt", "w").close()  # Create a new file with the map name
                            return text.strip()  # return the map name
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode

            input_surface.fill((30, 30, 30))
            txt_surface = font.render(text, True, color)
            width = max(400, txt_surface.get_width()+10)
            input_box.w = width
            input_surface.blit(txt_surface, (input_box.x+5, input_box.y+5))
            pygame.draw.rect(input_surface, color, input_box, 2)

            prompt = font.render("Enter Map Name:", True, (255, 255, 255))
            input_surface.blit(prompt, (100, 140))

            button_back.draw(input_surface)

            # Blit input_surface to screen
            screen.blit(input_surface, (0, 0))
            pygame.display.flip()

        return None
    


    ## INIT ## 
    rtk_thread = threading.Thread(target=launch_rtk_loop, daemon=True)
    rtk_thread.start()
    motor_driver = MotorDriver()
    speed = 0.4
    controls_font = pygame.font.Font(None, 28)
    control_panel_width = 210# Width of the control panel
    control_panel_height = 180# Height of the control panel
    control_panel_surface = pygame.Surface((control_panel_width, control_panel_height))
    control_panel_surface.set_alpha(150)  # Set transparency (0-255, where 255 is fully opaque)
    control_panel_surface.fill((0, 0, 0))  # Fill with black color

    file_path = write_new_map()
    if file_path is None:
        print("No file name provided. Returning to menu.")
        if rtk_thread and rtk_thread.is_alive():
            cleanup()
        pygame.event.clear()
        return STATE_MENU
    ## Main Loop ##
    running = True
    while running:
        screen.fill(GREEN1)

        ## Keys & Inputs ##
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    print("Up Arrow Pressed: Move Forward")
                    motor_driver.set_motor(speed, speed)
                elif event.key == pygame.K_DOWN:
                    print("Down Arrow Pressed: Move Backward")
                    motor_driver.set_motor(-speed, -speed)
                elif event.key == pygame.K_LEFT:
                    print("Left Arrow Pressed: Turn Left")
                    motor_driver.set_motor(-speed, speed)
                elif event.key == pygame.K_RIGHT:
                    print("Right Arrow Pressed: Turn Right")
                    motor_driver.set_motor(speed, -speed)
                elif event.key == pygame.K_0:
                    print("0 pressed: Activating Blade Motor")
                    motor_driver.set_blade(0.3)
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    print("Key Released: Stop Motors")
                    motor_driver.stop_motors()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_back.is_clicked(mouse_pos, True):
                    if rtk_thread and rtk_thread.is_alive():
                        cleanup()
                    pygame.event.clear()                   
                    running = False
                elif button_save_map.is_clicked(mouse_pos, True):
                    print("Saving map...")
                    if rtk_thread and rtk_thread.is_alive():
                        cleanup()
                    pygame.event.clear()
                    running = False
                elif button_delete_map.is_clicked(mouse_pos, True):
                    print("Deleting map...")
                    os.remove(file_path)
                    print("Map deleted.")
                    if rtk_thread and rtk_thread.is_alive():
                        cleanup()
                    pygame.event.clear()
                    running = False
                elif button_increase_speed.is_clicked(mouse_pos, True):
                    speed = min(speed + 0.1, 1.0)
                    print("Speed Increased!")
                elif button_decrease_speed.is_clicked(mouse_pos, True):
                    speed = max(speed - 0.1, 0.1)
                    print("Speed Decreased!")
        
        button_delete_map.draw(screen)
        button_save_map.draw(screen)
        button_increase_speed.draw(screen)
        button_decrease_speed.draw(screen)
        button_back.draw(screen)
        screen.blit(control_panel_surface, (20, 530))  # Position of the control panel
    
        ## Draw Controls ## 
        controls_text = [
            "Speed: " + str(round(speed*100,1))+ "%",
            "Controls: Arrow Keys",
            "Blade Act.: '0' Key",
        ]
        y_offset = 10  # Starting offset for text drawing (within the background)
        for line in controls_text:
            control_line = controls_font.render(line, True, (255, 255, 255))
            screen.blit(control_line, (30, 540 + y_offset))  # Adjust position within the panel
            y_offset += 30  # Move down for the next line

        ## Update Display (last) ##
        pygame.display.flip()

    ## Exit Process ##
    if rtk_thread and rtk_thread.is_alive():
        cleanup()
    print("Returning to main menu...")                 
    return STATE_MENU

def rc_mode():
    ## Function Setup ##
    pygame.event.clear()
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
                    motor_driver.set_motor(speed, speed)
                elif event.key == pygame.K_DOWN:
                    print("Down Arrow Pressed: Move Backward")
                    motor_driver.set_motor(-speed, -speed)
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
                if button_back.is_clicked(mouse_pos, True):
                    running = False
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
    print("Returning to main menu...") 
    return STATE_MENU

def run_menu():
    print("DEBUG menu screen activated")
    last_state = None
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