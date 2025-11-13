from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

WIN_W, WIN_H = 640, 800

diamond = {'x': 320, 'y': 650, 'size': 18, 'color': (1, 1, 0)}
catcher = {'x': 240, 'width': 160, 'color': (1, 1, 1)}
score = 0
fall_speed = 2
game_over = False
paused = False
pause_icon = True  # True: Pause icon দেখাও, False: Play icon দেখাও
base_speed = 2
speed_increase_per_score = 0.25

def draw_pixel(x, y, color):
    glColor3f(*color)
    glPointSize(2)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def zone_of_line(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0: return 0
        if dx < 0 and dy >= 0: return 3
        if dx < 0 and dy < 0: return 4
        return 7
    else:
        if dx >= 0 and dy >= 0: return 1
        if dx < 0 and dy >= 0: return 2
        if dx < 0 and dy < 0: return 5
        return 6

def to_zone0(x, y, zone):
    ops = [lambda x, y: (x, y),
           lambda x, y: (y, x),
           lambda x, y: (y, -x),
           lambda x, y: (-x, y),
           lambda x, y: (-x, -y),
           lambda x, y: (-y, -x),
           lambda x, y: (-y, x),
           lambda x, y: (x, -y)]
    return ops[zone](x, y)

def from_zone0(x, y, zone):
    ops = [lambda x, y: (x, y),
           lambda x, y: (y, x),
           lambda x, y: (-y, x),
           lambda x, y: (-x, y),
           lambda x, y: (-x, -y),
           lambda x, y: (-y, -x),
           lambda x, y: (y, -x),
           lambda x, y: (x, -y)]
    return ops[zone](x, y)

def midpoint_draw(x1, y1, x2, y2, color):
    zone = zone_of_line(x1, y1, x2, y2)
    tx1, ty1 = to_zone0(x1, y1, zone)
    tx2, ty2 = to_zone0(x2, y2, zone)
    if tx1 > tx2:
        tx1, ty1, tx2, ty2 = tx2, ty2, tx1, ty1
    dx, dy = tx2 - tx1, ty2 - ty1
    d = 2*dy - dx
    incE, incNE = 2*dy, 2*(dy-dx)
    y = ty1
    for x in range(tx1, tx2+1):
        px, py = from_zone0(x, y, zone)
        draw_pixel(px, py, color)
        if d < 0:
            d += incE
        else:
            d += incNE
            y += 1

def draw_arrow_left():
    # Teal color
    c = (0, 1, 1)
    midpoint_draw(45, 760, 65, 780, c)
    midpoint_draw(45, 760, 65, 740, c)
    midpoint_draw(45, 760, 90, 760, c)

def draw_pause_button():
    # Show pause or play icon depending on state
    if pause_icon:
        # Pause icon (Amber color)
        c = (1, 0.75, 0)
        midpoint_draw(300, 780, 300, 730, c)
        midpoint_draw(340, 780, 340, 730, c)
    else:
        # Play icon (Amber color) — right-pointing triangle
        c = (1, 0.75, 0)
        midpoint_draw(300, 780, 340, 755, c)
        midpoint_draw(340, 755, 300, 730, c)
        midpoint_draw(300, 730, 300, 780, c)

def draw_cross_button():
    csx, csy, hs = 615, 755, 15
    c = (1, 0, 0)
    midpoint_draw(csx - hs, csy - hs, csx + hs, csy + hs, c)
    midpoint_draw(csx - hs, csy + hs, csx + hs, csy - hs, c)

def random_bright_color():
    while True:
        c = [random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1)]
        # Ensure color is not too dark, and at least one channel strong for brightness
        if sum(c) > 2:
            return tuple(c)

def draw_diamond():
    global diamond
    x, y, s = diamond['x'], diamond['y'], diamond['size']
    color = diamond.get('color', (1, 1, 0))
    midpoint_draw(x, y + s, x + s, y, color)
    midpoint_draw(x + s, y, x, y - s, color)
    midpoint_draw(x, y - s, x - s, y, color)
    midpoint_draw(x - s, y, x, y + s, color)

def draw_catcher():
    cx = catcher['x']
    color = catcher['color']
    midpoint_draw(cx, 70, cx + 50, 100, color)
    midpoint_draw(cx + 50, 100, cx + 170, 100, color)
    midpoint_draw(cx + 170, 100, cx + 220, 70, color)
    midpoint_draw(cx + 220, 70, cx, 70, color)

def draw_score():
    glColor3f(1,1,1)
    glRasterPos2f(20, 780)
    for ch in f"Score: {score}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_arrow_left()
    draw_pause_button()
    draw_cross_button()
    draw_diamond()
    draw_catcher()
    draw_score()
    if game_over:
        glColor3f(1,0,0)
        glRasterPos2f(250, 410)
        for ch in "GAME OVER":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    elif paused:
        glColor3f(1,1,0)
        glRasterPos2f(250, 410)
        for ch in "PAUSED":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glutSwapBuffers()

def diamond_caught():
    cx = catcher['x']
    left = cx
    right = cx+220
    up_y = 100
    down_y = 70
    dx, dy = diamond['x'], diamond['y']-diamond['size']
    return (left < dx < right) and (down_y < dy < up_y)

def update(val=0):
    global diamond, score, game_over, fall_speed
    if not game_over and not paused:
        diamond['y'] -= fall_speed
        if diamond_caught():
            score += 1
            print(f"Score: {score}")
            diamond['x'] = random.randint(65, WIN_W-65)
            diamond['y'] = 650
            diamond['color'] = random_bright_color()
            fall_speed = base_speed + (score * speed_increase_per_score)
        elif diamond['y'] - diamond['size'] < 60:
            game_over_routine()
    glutPostRedisplay()
    glutTimerFunc(18, update, 0)

def game_over_routine():
    global game_over, catcher
    game_over = True
    catcher['color'] = (1, 0, 0)
    print(f"Game Over! Final Score: {score}")

def key_control(key, x, y):
    global catcher, game_over, paused
    if key == GLUT_KEY_LEFT and catcher['x'] > 10 and not game_over and not paused:
        catcher['x'] -= 25
    if key == GLUT_KEY_RIGHT and catcher['x'] < WIN_W-240 and not game_over and not paused:
        catcher['x'] += 25
    glutPostRedisplay()

def keyboard(key, x, y):
    if key == b'r':
        restart_game()

def restart_game():
    global game_over, score, diamond, catcher, paused, fall_speed
    game_over = False
    score = 0
    diamond['x'] = random.randint(65, WIN_W-65)
    diamond['y'] = 650
    diamond['color'] = random_bright_color()
    catcher['x'] = 240
    paused = False
    fall_speed = base_speed
    catcher['color'] = (1,1,1)
    print("Starting Over!")
    glutPostRedisplay()

def mouse(button, state, x, y):
    global paused, pause_icon
    mx, my = x, WIN_H - y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Cross(X): Exit
        if 600 <= mx <= 630 and 740 <= my <= 770:
            print(f"Goodbye! Final Score: {score}")
            glutLeaveMainLoop()
        # Pause area: pause/resume toggle
        if 300 <= mx <= 340 and 730 <= my <= 780:
            if not game_over:
                global paused
                paused = not paused
                # Toggle pause/play icon
                global pause_icon
                pause_icon = paused == False
        # Arrow (left): restart
        if (45 <= mx <= 90) and (740 <= my <= 780):
            restart_game()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(80, 40)
    glutCreateWindow(b"Catch the Diamonds!")
    glClearColor(0, 0, 0, 1)
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glutDisplayFunc(display)
    glutTimerFunc(0, update, 0)
    glutSpecialFunc(key_control)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMainLoop()

if __name__ == "__main__":
    main()