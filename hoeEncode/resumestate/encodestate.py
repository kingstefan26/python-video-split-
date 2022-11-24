class State:
    def __init__(self, filepath):
        self.filepath = filepath


currentState = None

def start(new_state):
    global currentState
    currentState = new_state


def invalidate():
    global currentState
    currentState = None
