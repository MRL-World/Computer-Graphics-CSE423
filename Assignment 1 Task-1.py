#TASK 01

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

angle = 0.0
bg_color = [0.0, 0.0, 0.0]
home_color = [1.0, 1.0, 1.0]
rain_speed = 2
rain_drops = [(random.uniform(0, 500), random.uniform(0, 500)) for i in range(1000)]

def check_line_1(x, y):
    x1, y1, x2, y2 = 150, 150, 250, 250
    dx = x2 - x1
    dy = y2 - y1
    m = dy / dx
    c = y1 - m * x1
    eqn = m * x + c
    if y - 10 > eqn:
        return True
    else:
        return False

def check_line_2(x, y):
    x1, y1, x2, y2 = 250, 250, 350, 150
    dx = x2 - x1
    dy = y2 - y1
    m = dy / dx
    c = y1 - m * x1
    eqn = m * x + c
    if y - 10 > eqn:
        return True
    else:
        return False

def drawRaindrop(x, y):
    global angle
    length = 8
    rotated_x = x + angle
    glBegin(GL_LINES)
    glVertex2f(rotated_x, y)
    glVertex2f(x, y + length)
    glEnd()

def drawRain():
    glColor3f(173 / 255, 216 / 255, 230 / 255)
    for x, y in rain_drops:
        if check_line_1(x, y) or check_line_2(x, y):
            glLineWidth(2)
            drawRaindrop(x, y)
        else:
            pass

def drawHouse():
    glLineWidth(4)

    glColor3f(0.7, 0.2, 0.1)
    glBegin(GL_TRIANGLES)
    glVertex2d(150, 200)
    glVertex2d(350, 200)
    glVertex2d(250, 300)
    glEnd()

    glColor3f(0.5, 0.3, 0.2)
    glBegin(GL_QUADS)
    glVertex2d(150, 200)
    glVertex2d(350, 200)
    glVertex2d(350, 50)
    glVertex2d(150, 50)
    glEnd()

    glColor3f(0.3, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2d(220, 120)
    glVertex2d(280, 120)
    glVertex2d(280, 50)
    glVertex2d(220, 50)
    glEnd()

    glColor3f(1.0, 1.0, 0.0)
    glPointSize(6.0)
    glBegin(GL_POINTS)
    glVertex2d(270, 85)
    glEnd()

    glColor3f(0.1, 0.4, 0.7)
    glBegin(GL_QUADS)
    glVertex2d(170, 170)
    glVertex2d(210, 170)
    glVertex2d(210, 130)
    glVertex2d(170, 130)
    glVertex2d(290, 170)
    glVertex2d(330, 170)
    glVertex2d(330, 130)
    glVertex2d(290, 130)
    glEnd()

    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex2d(190, 170)
    glVertex2d(190, 130)
    glVertex2d(170, 150)
    glVertex2d(210, 150)
    glVertex2d(310, 170)
    glVertex2d(310, 130)
    glVertex2d(290, 150)
    glVertex2d(330, 150)
    glEnd()

def specialKeyListener(key, x, y):
    global angle
    if key == GLUT_KEY_RIGHT:
        angle += 15
    elif key == GLUT_KEY_LEFT:
        angle -= 15
    elif key == GLUT_KEY_UP:
        bg_color[0] += 0.1
        bg_color[1] += 0.1
        bg_color[2] += 0.1
        home_color[0] -= 0.1
        home_color[1] -= 0.1
        home_color[2] -= 0.1
    elif key == GLUT_KEY_DOWN:
        if sum(bg_color) == 0 and sum(home_color) == 3:
            pass
        else:
            bg_color[0] -= 0.1
            bg_color[1] -= 0.1
            bg_color[2] -= 0.1
            home_color[0] += 0.1
            home_color[1] += 0.1
            home_color[2] += 0.1
    glutPostRedisplay()

def animate():
    glutPostRedisplay()
    global rain_drops, rain_speed
    for i in range(len(rain_drops)):
        x, y = rain_drops[i]
        rain_drops[i] = (x, y - rain_speed)
        if y - rain_speed < 150:
            rain_drops[i] = (random.uniform(0, 500), random.uniform(150, 500))

def setup():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    global bg_color, home_color
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup()
    glClearColor(*bg_color, 1.0)
    glColor3f(home_color[0], home_color[0], home_color[0])
    drawHouse()
    drawRain()
    glutSwapBuffers()

glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(500, 500)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Rainy House")
glutDisplayFunc(showScreen)
glutIdleFunc(animate)
glutSpecialFunc(specialKeyListener)
glutMainLoop()
