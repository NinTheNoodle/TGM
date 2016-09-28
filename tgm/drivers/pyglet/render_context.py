import pyglet
import tkinter as tk
from pyglet import gl
from itertools import cycle
import gc


def next_power_of_2(x):
    if x == 0:
        return 0
    return 1 << ((x - 1).bit_length())


class Manager:
    initialized = False

    @classmethod
    def init(cls):
        if cls.initialized:
            return
        cls.initialized = True

        cls.time_passed = 0
        cls.frame_dt = 0
        cls.target_fps = 0
        cls.fps_list = []
        cls.update_function = None

        cls.tk_root = tk.Tk()

        cls.atlas = TextureAtlas(4096)
        cls._target = create_texture(1024, 1024)
        cls.buffer_manager = pyglet.image.get_buffer_manager()
        cls.col_buffer = cls.buffer_manager.get_color_buffer()

        cls.vertex_list_2d = pyglet.graphics.vertex_list_indexed(
            0, [], "v2f/stream", "c4f/stream", "t2f/stream")
        cls.quad = pyglet.graphics.vertex_list_indexed(
            4,
            [0, 1, 2, 0, 2, 3],
            ("v2f/stream", [0, 0, 1, 0, 1, 1, 0, 1]),
            ("t2f/stream", [0, 0, 1, 0, 1, 1, 0, 1])
        )
        cls.default_texture = Texture(1, 1)
        cls.default_texture.start_draw()
        clear_color(1, 1, 1, 1)
        cls.default_texture.end_draw()

        pyglet.clock.schedule(cls._refresh)

    @classmethod
    def get_target(cls, width, height):
        if width > cls._target.width or height > cls._target.height:
            size = next_power_of_2(max(width, height))
            cls._target = create_texture(size, size)
        return cls._target

    @classmethod
    def _refresh(cls, dt):
        if cls.update_function is None:
            return

        if cls.time_passed < 2 / cls.target_fps:
            cls.time_passed += dt

        cls.frame_dt += dt
        if cls.time_passed >= 1 / cls.target_fps:
            cls.fps_list.insert(0, cls.frame_dt)
            if len(cls.fps_list) > cls.target_fps:
                del cls.fps_list[-1]
            fps = len(cls.fps_list) / sum(cls.fps_list)

            cls.update_function(cls.frame_dt, fps)

            cls.frame_dt = 0
            cls.time_passed -= 1 / cls.target_fps


def bind_texture_region(texture, x, y, w, h, premultiplied=False, flip=False):
    gl.glTexParameteri(
        gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(
        gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glEnable(gl.GL_SCISSOR_TEST)

    gl.glEnable(gl.GL_BLEND)
    if premultiplied:
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)

    else:
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA,
                               gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    gl.glViewport(x, y, w, h)
    gl.glScissor(x, y, w, h)

    gl.glBindFramebufferEXT(
        gl.GL_DRAW_FRAMEBUFFER_EXT,
        Manager.col_buffer.gl_buffer
    )

    gl.glFramebufferTexture2DEXT(
        gl.GL_DRAW_FRAMEBUFFER_EXT,
        gl.GL_COLOR_ATTACHMENT0_EXT,
        texture.target,
        texture.id,
        0
    )

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    if flip:
        gl.gluOrtho2D(0, w, h, 0)
    else:
        gl.gluOrtho2D(0, w, 0, h)


def draw_texture_region(texture, u1, v1, u2, v2, x1, y1, x2, y2):
    u1 /= texture.width
    u2 /= texture.width
    v1 /= texture.height
    v2 /= texture.height
    Manager.quad.vertices = [x1, y1, x2, y1, x2, y2, x1, y2]
    Manager.quad.tex_coords = [u1, v1, u2, v1, u2, v2, u1, v2]
    draw_vertex_list(Manager.quad, texture)


def clear_color(r, g, b, a):
    gl.glClearColor(r, g, b, a)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)


def bind_window(w, h):
    gl.glBindFramebufferEXT(gl.GL_DRAW_FRAMEBUFFER_EXT, 0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gl.glViewport(0, 0, w, h)
    gl.glScissor(0, 0, w, h);
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluOrtho2D(0, w, h, 0)


def draw_vertex_list(vertex_list, texture):
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture.id)
    vertex_list.draw(gl.GL_TRIANGLES)


def create_texture(w, h):
    return pyglet.image.Texture.create(
        w, h, internalformat=gl.GL_RGBA
    )


def resize_texture(texture, w, h):
    new_texture = create_texture(w, h)
    bind_texture_region(new_texture, 0, 0, w, h)
    draw_texture_region(
        texture,
        0, 0, texture.width, texture.height,
        0, 0, texture.width, texture.height
    )
    return new_texture


class TextureAtlas:
    def __init__(self, size):
        self.texture = create_texture(size, size)
        self.size = size
        self.cells = [(0, 0, size, size)]

    def aquire_cell(self, width, height):
        target_cell_size = next_power_of_2(max(width, height))
        find_size = target_cell_size

        while True:
            while find_size <= self.size:
                for i, cell in enumerate(self.cells):
                    if cell[2] - cell[0] == find_size:
                        while find_size > target_cell_size:
                            cells = self._split_cell(self.cells[i])
                            self.cells[i:i + 1] = cells
                            find_size //= 2

                        cell = self.cells.pop(i)
                        return (
                            cell[0],
                            cell[1],
                            cell[0] + width,
                            cell[1] + height
                        )
                find_size *= 2

            find_size = max(target_cell_size, self.size)
            self.size_up()

    def size_up(self):
        self.size *= 2
        new_size = self.size
        old_size = new_size // 2

        self.release_cell((old_size, old_size, new_size, new_size))
        self.release_cell((0, old_size, old_size, new_size))
        self.release_cell((old_size, 0, new_size, old_size))

        self.texture = resize_texture(self.texture, self.size, self.size)
        print("RESIZE", self.size)

    def release_cell(self, cell):
        size = next_power_of_2(max(cell[2] - cell[0], cell[3] - cell[1]))
        cell = (
            cell[0],
            cell[1],
            cell[0] + size,
            cell[1] + size
        )
        self.cells.insert(0, cell)

        parent_size = size * 2
        x1 = (cell[0] // parent_size) * parent_size
        y1 = (cell[1] // parent_size) * parent_size
        parent_cell = (x1, y1, x1 + parent_size, y1 + parent_size)

        siblings = self._split_cell(parent_cell)

        if all(sibling in self.cells for sibling in siblings):
            for sibling in reversed(siblings):
                self.cells.remove(sibling)
            self.release_cell(parent_cell)

    def _split_cell(self, cell):
        x1, y1, x2, y2 = cell
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2

        return [
            (x1, y1, mid_x, mid_y),
            (mid_x, y1, x2, mid_y),
            (x1, mid_y, mid_x, y2),
            (mid_x, mid_y, x2, y2)
        ]


def set_update_function(function, fps):
    Manager.update_function = function
    set_fps(fps)


def set_fps(fps):
    Manager.target_fps = fps


def load_texture(path):
    image = pyglet.image.load(path)
    texture = Texture(image.width, image.height)
    bind_texture_region(
        Manager.atlas.texture,
        texture.cell[0], texture.cell[1],
        texture.width, texture.height,
        flip=True
    )
    clear_color(0, 0, 0, 0)
    image.blit(0, 0)
    return texture


def run():
    pyglet.app.run()
    gc.collect()


class Texture:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._new_size = (width, height)

        Manager.init()

        self.draw_calls = []
        self.cell = Manager.atlas.aquire_cell(width, height)

    def add_draw_2d(self, texture, indices, vertices, colors, uvs):
        if texture is None:
            texture = Manager.default_texture

        x, y = texture.cell[:2]
        # bounds = [(x + 0.5, texture.width - 1), (y + 0.5, texture.height - 1)]
        bounds = [(x, texture.width), (y, texture.height)]

        global_uvs = (
            start + size * factor
            for factor, (start, size) in zip(uvs, cycle(bounds))
        )

        if not self._is_last_draw_action(self._action_draw_2d):
            self.draw_calls.append((self._action_draw_2d, [], [], [], []))

        draw_call = self.draw_calls[-1]
        draw_call[1].extend(len(draw_call[2]) // 2 + index for index in indices)
        draw_call[2].extend(vertices)
        draw_call[3].extend(colors)
        draw_call[4].extend(global_uvs)

    def update(self):
        if (self.width, self.height) != self._new_size:
            self._resize(*self._new_size)

        self.start_draw()
        for draw_call in self.draw_calls:
            draw_call[0](*draw_call[1:])
        self.draw_calls = []
        self.end_draw()

    def resize(self, width, height):
        self._new_size = (width, height)

    def _resize(self, width, height):
        x1, y1, x2, y2 = self.cell

        target = Manager.get_target(self.width, self.height)

        bind_texture_region(target, 0, 0, self.width, self.height)
        clear_color(0, 0, 0, 0)
        draw_texture_region(
            Manager.atlas.texture,
            x1, y1, x2, y2,
            0, 0, self.width, self.height
        )

        Manager.atlas.release_cell(self.cell)
        self.cell = Manager.atlas.aquire_cell(width, height)
        x, y = self.cell[:2]

        bind_texture_region(Manager.atlas.texture, x, y, width, height)
        clear_color(0, 0, 0, 0)

        draw_texture_region(
            target,
            0, 0, self.width, self.height,
            0, 0, self.width, self.height
        )
        self.width = width
        self.height = height

    def add_clear(self, red=0, green=0, blue=0, alpha=0):
        if not self._is_last_draw_action(self._action_clear):
            self.draw_calls.append(
                (self._action_clear, red, green, blue, alpha)
            )

    def _action_draw_2d(self, indices, vertices, colors, uvs):
        Manager.vertex_list_2d.resize(len(vertices) // 2, len(indices))
        Manager.vertex_list_2d.indices = indices
        Manager.vertex_list_2d.vertices = vertices
        Manager.vertex_list_2d.colors = colors
        Manager.vertex_list_2d.tex_coords = [
            coord / Manager.atlas.size for coord in uvs
            ]
        draw_vertex_list(Manager.vertex_list_2d, Manager.atlas.texture)

    def _action_clear(self, r, g, b, a):
        clear_color(r, g, b, a)

    def start_draw(self):
        bind_texture_region(
            Manager.get_target(self.width, self.height),
            0, 0, self.width, self.height
        )

    def end_draw(self):
        x, y = self.cell[:2]
        bind_texture_region(
            Manager.atlas.texture, x, y, self.width, self.height,
            premultiplied=True
        )
        clear_color(0, 0, 0, 0)
        draw_texture_region(
            Manager.get_target(self.width, self.height),
            0, 0, self.width, self.height, 0, 0, self.width, self.height
        )

    def _is_last_draw_action(self, fnc):
        try:
            return self.draw_calls[-1][0] == fnc
        except IndexError:
            return False

    def destroy(self):
        Manager.atlas.release_cell(self.cell)

    def __del__(self):
        self.destroy()


class Window(Texture):
    def __init__(self, width, height, caption="", resizable=True):
        super().__init__(width, height)
        self.window = pyglet.window.Window(
            width, height, caption=caption, resizable=resizable, vsync=False
        )

        self.caption = caption
        self.mouse_x = width // 2
        self.mouse_y = height // 2
        self.mouse_buttons = set()
        self.keys = set()

        mouse_button_mapping = {
            pyglet.window.mouse.LEFT: "left",
            pyglet.window.mouse.MIDDLE: "middle",
            pyglet.window.mouse.RIGHT: "right"
        }

        @self.window.event
        def on_draw():
            x1, y1, x2, y2 = self.cell
            bind_window(self.window.width, self.window.height)
            clear_color(0, 0, 0, 1)
            draw_texture_region(
                Manager.atlas.texture,
                x1, y1, x2, y2,
                0, 0, self.window.width, self.window.height
            )

        @self.window.event
        def on_resize(width, height):
            self.resize(width, height)
            self.window.invalid = False

        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            self.mouse_buttons.add(mouse_button_mapping[button])

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            try:
                self.mouse_buttons.remove(mouse_button_mapping[button])
            except KeyError:
                pass

        @self.window.event
        def on_key_press(symbol, modifiers):
            self.keys.add(symbol)

        @self.window.event
        def on_key_release(symbol, modifiers):
            try:
                self.keys.remove(symbol)
            except KeyError:
                pass

    def update(self):
        mx, my = Manager.tk_root.winfo_pointerxy()
        wx, wy = self.window.get_location()
        self.mouse_x = mx - wx
        self.mouse_y = my - wy
        super().update()

    def _resize(self, width, height):
        super()._resize(width, height)
        self.window.set_size(width, height)

    def set_caption(self, caption):
        self.window.set_caption(caption)
        self.caption = caption
