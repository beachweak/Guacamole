import pyglet
import math
import re
import clipboard
import sys
import os
from pyglet.gl import *
from pyglet.window import key, mouse
from pyglet.window import Window
import pyglet.shapes
from ctypes import c_float

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

icon_path = resource_path('favicon.ico')
icon = pyglet.image.load(icon_path)

config = pyglet.gl.Config(double_buffer=True)
window = pyglet.window.Window(caption="Guacamole", width=1280, height=720, config=config, resizable=True)

window.set_icon(icon)


glEnable(GL_DEPTH_TEST)

rotation = [0, 0, 0]
typing = False  
command = ""

batch = pyglet.graphics.Batch()

shape = 'cube'

console_height = window.height // 2  # half of the window height
label_console = pyglet.text.Label('console', font_size=14, x=10, y=window.height - console_height,
                                  anchor_x='left', anchor_y='center', color=(255, 255, 255, 255), batch=batch)
label_prompt = pyglet.text.Label('> ', font_size=12, x=10, y=console_height - 20,
                                  anchor_x='left', anchor_y='center', color=(255, 255, 255, 255), batch=batch)
label_command = pyglet.text.Label('', font_size=12, x=30, y=console_height - 20,
                                   anchor_x='left', anchor_y='center', color=(255, 255, 255, 255), batch=batch)

cursor = pyglet.shapes.Line(0, 0, 0, 0, width=1, color=(255, 255, 255), batch=batch)
cursor.visible = False

def custom_print(msg):
    global console_output
    document = console_output.document
    console_output.text += msg + '\n'
    document.set_style(0, len(document.text), dict(color=label_console.color))

@window.event
def on_text_motion(motion):
    global command, typing
    if typing and motion == key.MOTION_BACKSPACE:
        command = command[:-1]
    label_command.text = command

@window.event
def on_key_press(symbol, modifiers):
    global command, typing
    if symbol == key.ENTER:
        typing = False
        handle_command(command.strip())  # use handle_command instead of process_command
        command = ""
    elif symbol == key.V and (modifiers & key.MOD_CTRL):
        paste_text = clipboard.paste()
        if paste_text:
            command += paste_text
    label_command.text = command

def toggle_cursor_visibility(dt):
    global cursor
    if typing:
        cursor.visible = not cursor.visible
    else:
        cursor.visible = False

color_options = {
    'Red': (1, 0, 0),
    'White': (1, 1, 1),
    'Rainbow': 'Rainbow'
}

cube_color = color_options['White']

bg_color_options = {
    'Black': (0, 0, 0, 1),
    'White': (1, 1, 1, 1),
    'Gray': (0.5, 0.5, 0.5, 1)
}

bg_color = bg_color_options['Black']

def draw_rainbow_cube():
    glBegin(GL_QUADS)
    for i, face in enumerate(cube_faces):
        glColor3f(*rainbow_colors[i])
        for vertex in face:
            glVertex3fv((GLfloat * len(cube_vertices[vertex]))(*cube_vertices[vertex]))
    glEnd()

rainbow_colors = [
    (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, 0, 1), (0, 1, 1)
]

def draw_rainbow_sphere():
    num_slices = 10
    num_stacks = 10
    radius = 1

    for stack in range(num_stacks):
        phi1 = (stack / num_stacks) * math.pi
        phi2 = ((stack + 1) / num_stacks) * math.pi
        for slice in range(num_slices):
            theta1 = (slice / num_slices) * 2 * math.pi
            theta2 = ((slice + 1) / num_slices) * 2 * math.pi

            glBegin(GL_TRIANGLE_STRIP)
            for theta, phi in [(theta1, phi1), (theta2, phi1), (theta1, phi2), (theta2, phi2)]:
                x = radius * math.sin(phi) * math.cos(theta)
                y = radius * math.sin(phi) * math.sin(theta)
                z = radius * math.cos(phi)

                glColor3f(math.sin(theta) * 0.5 + 0.5, math.sin(theta + 2 * math.pi / 3) * 0.5 + 0.5, math.sin(theta - 2 * math.pi / 3) * 0.5 + 0.5)
                glVertex3f(x, y, z)
            glEnd()

def draw_rainbow_pyramid():
    glBegin(GL_TRIANGLES)
    for face in pyramid_faces[:4]:
        for vertex in face:
            glColor3f(*calculate_rainbow_color(pyramid_vertices[vertex]))
            glVertex3fv((GLfloat * len(pyramid_vertices[vertex]))(*pyramid_vertices[vertex]))
    glEnd()

    glBegin(GL_QUADS)
    for face in pyramid_faces[4:]:
        for vertex in face:
            glColor3f(*calculate_rainbow_color(pyramid_vertices[vertex]))
            glVertex3fv((GLfloat * len(pyramid_vertices[vertex]))(*pyramid_vertices[vertex]))
    glEnd()

def draw_rainbow_cone():
    glBegin(GL_TRIANGLES)
    for face in cone_faces:
        for vertex in [cone_vertices[0], cone_base_vertices[face[1]], cone_base_vertices[face[2]]]:
            glColor3f(*calculate_rainbow_color(vertex))
            glVertex3fv((GLfloat * len(vertex))(*vertex))
    glEnd()

def draw_rainbow_cylinder():
    glBegin(GL_QUADS)
    for face in cylinder_faces:
        for vertex in [cylinder_vertices[i] for i in face]:
            glColor3f(*calculate_rainbow_color(vertex))
            glVertex3fv((GLfloat * len(vertex))(*vertex))
    glEnd()

    # Draw top and bottom
    for z_pos in [1, -1]:
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(*calculate_rainbow_color((0, z_pos, 0)))
        glVertex3f(0, z_pos, 0)
        for i in range(num_slices):
            index = i if z_pos == 1 else i + num_slices
            vertex = cylinder_vertices[index]
            glColor3f(*calculate_rainbow_color(vertex))
            glVertex3fv((GLfloat * len(vertex))(*vertex))
        # Close the triangle fan
        vertex = cylinder_vertices[0] if z_pos == 1 else cylinder_vertices[num_slices]
        glColor3f(*calculate_rainbow_color(vertex))
        glVertex3fv((GLfloat * len(vertex))(*vertex))
        glEnd()


def calculate_rainbow_color(vertex):
    x, y, z = vertex
    r = math.sin(x) * 0.5 + 0.5
    g = math.sin(y + math.pi / 2) * 0.5 + 0.5
    b = math.sin(z + math.pi) * 0.5 + 0.5
    return r, g, b

@window.event
def on_text(text):
    global command, typing
    if typing:
        if text == '\r':
            handle_command(command)
            command = ""
        elif text == '\x08':
            command = command[:-1]
        else:
            command += text
            typing = True
        label_command.text = command

@window.event
def on_mouse_press(x, y, button, modifiers):
    global typing
    if button == mouse.LEFT:
        if label_console.y - 30 < y < label_console.y:
            typing = True
        else:
            typing = False

def set_2d_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, window.width, 0, window.height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def set_3d_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, window.width / window.height, 0.1, 100)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

@window.event
def on_draw():
    glClearColor(*bg_color)
    window.clear()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glEnable(GL_DEPTH_TEST)

    set_3d_projection()
    glTranslatef(0, 0, -5)
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)

    shape_color = cube_color

    if shape == 'cube':
        if shape_color == color_options['Rainbow']:
            draw_rainbow_cube()
        else:
            glColor3f(*shape_color)
            draw_cube()
    elif shape == 'sphere':
        if shape_color == color_options['Rainbow']:
            draw_rainbow_sphere()
        else:
            glColor3f(*shape_color)
            draw_sphere()
    elif shape == 'pyramid':
        if shape_color == color_options['Rainbow']:
            draw_rainbow_pyramid()
        else:
            glColor3f(*shape_color)
            draw_pyramid()
    elif shape == 'cone':
        if shape_color == color_options['Rainbow']:
            draw_rainbow_cone()
        else:
            glColor3f(*shape_color)
            draw_cone()
    elif shape == 'cylinder':
        if shape_color == color_options['Rainbow']:
            draw_rainbow_cylinder()
        else:
            glColor3f(*shape_color)
            draw_cylinder()

    glDisable(GL_DEPTH_TEST)

    set_2d_projection()

    label_console.y = window.height - 20
    label_prompt.y = window.height - 40
    label_command.y = window.height - 40

    cursor.x = label_command.x + label_command.content_width + 2
    cursor.y1 = label_command.y
    cursor.y2 = label_command.y + label_command.content_height

    if cursor.visible:
        cursor.draw()

    console_output.draw()

    batch.draw()

def toggle_cursor_visibility(dt):
    global cursor
    if typing:
        cursor.visible = not cursor.visible
    else:
        cursor.visible = False

    window.dispatch_event('on_draw')

# Handle commands entered in the embedded command-line interface
def handle_command(cmd):
    global cube_color, bg_color, shape
    cmd_parts = cmd.lower().split()  # Convert command to lowercase

    if len(cmd_parts) == 0:
        return

    if cmd_parts[0] == 'color':
        if len(cmd_parts) == 2:
            if cmd_parts[1].capitalize() in color_options.keys():
                cube_color = color_options[cmd_parts[1].capitalize()]
            elif re.match(r'^(#)?(?:[0-9a-fA-F]{3}){1,2}$', cmd_parts[1]):
                hex_color = cmd_parts[1].lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
                cube_color = rgb_color
            else:
                custom_print("Invalid color. Use a valid hex code or one of the available colors: red, white, rainbow.")
        else:
            custom_print("Invalid color. Use a valid hex code or one of the available colors: red, white, rainbow.")
    elif cmd_parts[0] == 'background':
        if len(cmd_parts) == 2:
            if cmd_parts[1].capitalize() in bg_color_options.keys():
                bg_color = bg_color_options[cmd_parts[1].capitalize()]
            elif re.match(r'^(#)?(?:[0-9a-fA-F]{3}){1,2}$', cmd_parts[1]):
                hex_color = cmd_parts[1].lstrip('#')
                rgb_color = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
                bg_color = (*rgb_color, 1)
            else:
                custom_print("Invalid background color. Use a valid hex code or one of the available colors: black, white, gray.")
            # Change console text color based on the background color
            if cmd_parts[1] == 'white':
                text_color = (0, 0, 0, 255)
            else:
                text_color = (255, 255, 255, 255)

            label_console.color = text_color
            label_prompt.color = text_color
            label_command.color = text_color
            console_output.color = text_color
        else:
            custom_print("Invalid background color. Use a valid hex code or one of the available colors: black, white, gray.")
    elif cmd_parts[0] == 'shape':
     if len(cmd_parts) == 2 and cmd_parts[1] in ['cube', 'sphere', 'pyramid', 'cone', 'cylinder']:
        shape = cmd_parts[1]
     else:
        custom_print("Invalid shape. Available shapes: cube, sphere, pyramid, cone, cylinder.")
    elif cmd_parts[0] == 'help':
        custom_print("Available commands:")
        custom_print("  color <color_name> - Set cube color. Available colors: red, white, rainbow. Hex value also accepted.")
        custom_print("  background <bg_color_name> - Set background color. Available colors: black, white, gray. Hex value also accepted.")
        custom_print("  shape <shape_name> - Set shape. Available shapes: cube, sphere, pyramid, cone, cylinder.")
        custom_print("  clear - Clear the console.")
    elif cmd_parts[0] == 'clear':
        console_output.document.text = ''
    else:
        custom_print("Invalid command. Type 'help' for a list of available commands.")

console_document = pyglet.text.document.FormattedDocument('')
console_document.set_style(0, len(console_document.text), dict(color=label_console.color))

console_output = pyglet.text.DocumentLabel(document=console_document,
                                           x=10, y=window.height/2-label_console.content_height/2, 
                                           width=window.width-20, multiline=True, anchor_x='left')

def draw_cube():
    glBegin(GL_QUADS)
    for face in cube_faces:
        for vertex in face:
            glVertex3fv((GLfloat * len(cube_vertices[vertex]))(*cube_vertices[vertex]))
    glEnd()

def draw_sphere():
    num_slices = 10
    num_stacks = 10
    radius = 1
    for stack in range(num_stacks):
        phi1 = (stack / num_stacks) * math.pi
        phi2 = ((stack + 1) / num_stacks) * math.pi
        for slice in range(num_slices):
            theta1 = (slice / num_slices) * 2 * math.pi
            theta2 = ((slice + 1) / num_slices) * 2 * math.pi
            
            glBegin(GL_TRIANGLE_STRIP)
            for theta, phi in [(theta1, phi1), (theta2, phi1), (theta1, phi2), (theta2, phi2)]:
                x = radius * math.sin(phi) * math.cos(theta)
                y = radius * math.sin(phi) * math.sin(theta)
                z = radius * math.cos(phi)
                glVertex3f(x, y, z)
            glEnd()

def draw_pyramid():
    glBegin(GL_TRIANGLES)
    for face in pyramid_faces[:4]:
        for vertex in face:
            glVertex3fv((GLfloat * len(pyramid_vertices[vertex]))(*pyramid_vertices[vertex]))
    glEnd()

    glBegin(GL_QUADS)
    for face in pyramid_faces[4:]:
        for vertex in face:
            glVertex3fv((GLfloat * len(pyramid_vertices[vertex]))(*pyramid_vertices[vertex]))
    glEnd()

def draw_cone():
    glBegin(GL_TRIANGLES)
    for face in cone_faces:
        for vertex in [cone_vertices[0], cone_base_vertices[face[1]], cone_base_vertices[face[2]]]:
            glVertex3fv((GLfloat * len(vertex))(*vertex))
    glEnd()

def draw_cylinder(shape_color=None):
    if shape_color is None:
        shape_color = cube_color

    if shape_color == color_options['Rainbow']:
        draw_rainbow_cylinder()
    else:
        glBegin(GL_QUADS)
        for face in cylinder_faces:
            glColor3f(*shape_color)
            for vertex in [cylinder_vertices[i] for i in face]:
                glVertex3fv((GLfloat * len(vertex))(*vertex))
        glEnd()

        # Draw top and bottom
        for z_pos in [1, -1]:
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(*shape_color)
            glVertex3f(0, z_pos, 0)
            base_vertices = [cylinder_vertices[i] for i in range(2 * num_slices) if cylinder_vertices[i][1] == z_pos]
            for vertex in (base_vertices if z_pos == 1 else base_vertices[::-1]):
                glVertex3fv((GLfloat * len(vertex))(*vertex))
            # Add the first vertex again to close the fan
            glVertex3fv((GLfloat * len(base_vertices[0]))(*base_vertices[0]))
            glEnd()

def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if buttons & pyglet.window.mouse.LEFT:
        rotation[0] -= dy * 0.3
        rotation[1] -= dx * 0.3
        rotation[2] += (dx + dy) * 0.15
    
window.push_handlers(on_mouse_drag)

cube_vertices = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
]

cube_faces = [
    (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
    (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
]

pyramid_vertices = [
    (0, 1, 0), (-1, -1, 1), (1, -1, 1),
    (1, -1, -1), (-1, -1, -1)
]

pyramid_faces = [
    (0, 1, 2), (0, 2, 3), (0, 3, 4),
    (0, 4, 1), (1, 4, 3, 2)
]

cone_vertices = [
    (0, 1, 0), 
]

cone_base_vertices = [
    (math.cos(2 * math.pi * i / 20), -1, math.sin(2 * math.pi * i / 20))
    for i in range(20)
]

cone_faces = [
    (0, i % 20, (i + 1) % 20) for i in range(20)
]


num_slices = 20
cylinder_vertices = [
    (math.cos(2 * math.pi * i / num_slices), 1, math.sin(2 * math.pi * i / num_slices))
    for i in range(num_slices)
] + [
    (math.cos(2 * math.pi * i / num_slices), -1, math.sin(2 * math.pi * i / num_slices))
    for i in range(num_slices)
]

cylinder_faces = [
    (i, (i + 1) % num_slices, (i + 1) % num_slices + num_slices, i + num_slices) for i in range(num_slices)
]

pyglet.app.run()
