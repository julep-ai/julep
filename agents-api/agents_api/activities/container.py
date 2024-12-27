class State:
    pass


class Container:
    state: State

    def __init__(self):
        self.state = State()


container = Container()
