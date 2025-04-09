import pygame
from motor_driver import MotorDriver
from menu import run_menu, Button
from states import RCMode, Mapping
from picamera2 import Picamera2



def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    motor_driver = MotorDriver()

    # Create the menu and add buttons
    menu = run_menu()
    menu.add_button(Button("RC-Mode", 100, 100, 400, 50, action="start_rc_mode"))
    menu.add_button(Button("Mapping-Mode", 100, 200, 400, 50, action="start_mapping"))
    menu.add_botton(Button("Pathing", 100, 300, 400, 50, action="start_pathing"))
    menu.add_button(Button("Sentry-Mode"), )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left-click
                    if menu.buttons[0].is_clicked(event.pos):
                        current_state = RCMode()
                    elif menu.buttons[1].is_clicked(event.pos):
                        current_state = Mapping()

        # Draw the menu
        menu.draw()

        # Run the current state
        current_state.run(screen, motor_driver)

    pygame.quit()

if __name__ == "__main__":
    main()