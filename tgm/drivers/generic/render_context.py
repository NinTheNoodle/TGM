def load_texture(path):
    pass


def set_update_function(function, fps):
    pass


def set_fps(fps):
    pass


def run():
    pass


class Texture:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def add_draw_2d(self, texture, indices, vertices, colors, uvs):
        pass

    def update(self):
        pass

    def resize(self, width, height):
        pass

    def add_clear(self, red=0, green=0, blue=0, alpha=0):
        pass

    def destroy(self):
        pass

    def __del__(self):
        self.destroy()


class Window(Texture):
    def __init__(self, width, height, caption="", resizable=False):
        self.mouse_x = width // 2
        self.mouse_y = height // 2
        self.caption = caption
        self.mouse_buttons = set()
        self.keys = set()

    def set_caption(self, caption):
        self.caption = caption
