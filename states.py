class State:
    def run(self):
        raise NotImplementedError("Each state should implement the run method")

class RCMode(State):
    def run(self, screen, motor_driver):
        # Handle the RC mode operations, such as accepting user input
        # Update the screen with information, etc.
        pass

class Mapping(State):
    def run(self, screen, motor_driver):
        # Handle the mapping logic
        pass