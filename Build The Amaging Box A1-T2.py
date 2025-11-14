from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

WIN_WIDTH, WIN_HEIGHT = 600, 600
balls = []
ball_speed = 0.05
color_flag = False
is_paused = False

def convert_coords(x, y):
    return x, WIN_HEIGHT - y

def toggle_color(dummy):  # Modified to accept the 'dummy' argument
    global color_flag
    color_flag = not color_flag
    glutPostRedisplay()

def mouse_click(button, state, x, y):
    global balls, is_paused, color_flag
    if not is_paused:
        if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            balls.append({
                'pos': convert_coords(x, y),
                'dir': (random.choice([-1, 1]), random.choice([-1, 1])),
                'col': (random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1))
            })
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            color_flag = True
            glutTimerFunc(1000, toggle_color, 0)  # This line remains the same
    glutPostRedisplay()

def special_keys(key, x, y):
    global ball_speed, is_paused
    if not is_paused:
        if key == GLUT_KEY_UP:
            ball_speed *= 1.5
        if key == GLUT_KEY_DOWN:
            ball_speed /= 1.5
    glutPostRedisplay()

def keyboard(key, x, y):
    global is_paused
    if key == b' ':
        is_paused = not is_paused
    glutPostRedisplay()

def setup():
    glViewport(0, 0, WIN_WIDTH, WIN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, WIN_WIDTH, 0.0, WIN_HEIGHT, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def draw():
    global balls, color_flag
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup()
    if balls:
        for ball in balls:
            x, y = ball['pos']
            glPointSize(8.0)
            glBegin(GL_POINTS)
            if color_flag:
                glColor3f(0.2, 0.2, 0.2)
            else:
                glColor3f(ball['col'][0], ball['col'][1], ball['col'][2])
            glVertex2f(x, y)
            glEnd()
    glutSwapBuffers()

def update():
    glutPostRedisplay()
    global balls, ball_speed, WIN_WIDTH, WIN_HEIGHT, is_paused
    if not is_paused:
        for ball in balls:
            x, y = ball['pos']
            dx, dy = ball['dir']
            x += dx * ball_speed
            y += dy * ball_speed
            if x < 0 or x > WIN_WIDTH:
                ball['dir'] = (-dx, dy)
            if y < 0 or y > WIN_HEIGHT:
                ball['dir'] = (dx, -dy)
            ball['pos'] = (x, y)

glutInit()
glutInitWindowSize(WIN_WIDTH, WIN_HEIGHT)
glutInitWindowPosition(0, 0)
glutInitDisplayMode(GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGB)
glutCreateWindow(b"Bouncing Balls")

glutDisplayFunc(draw)
glutIdleFunc(update)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_keys)
glutMouseFunc(mouse_click)

glutMainLoop()