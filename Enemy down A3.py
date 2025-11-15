from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, time, random

# --------------------
# GLOBAL SETTINGS
# --------------------
hero_position = [0.0, 0.0, 0.0]  # x, y, z
hero_angle = 0.0
eye_height = 15.0
ammo_list = []f
foe_list = []
spark_list = []
auto_mode = False
fp_camera = False
cheat_mode = False
auto_gun_follow = False
cam_angle = 0
cam_height = 800
last_fire_time = 0

score = 0
lives = 5
missed_shots = 0
end_flag = False
end_printed = False

MAX_FOES = 5
MAX_MISSED = 10
ARENA_SIZE = 1000

# --------------------
# BULLET CUBES
# --------------------
def make_bullet(x, y, z, angle, target=None):
    return {
        'x': x, 'y': y, 'z': z,
        'angle': angle,
        'born': time.time(),
        'hit': False,
        'hit_target': False,
        'lock': target
    }

def update_bullet(b):
    if b['hit']:
        return
    speed = 5
    if b['lock'] and not b['lock']['down']:
        dx = b['lock']['x'] - b['x']
        dy = b['lock']['y'] - b['y']
        dz = b['lock']['z'] - b['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist > 0:
            b['x'] += (dx/dist) * speed
            b['y'] += (dy/dist) * speed
            b['z'] += (dz/dist) * speed
    else:
        nx = b['x'] + speed * math.sin(math.radians(b['angle']))
        nz = b['z'] + speed * math.cos(math.radians(b['angle']))
        half = (ARENA_SIZE/2) - 5
        if abs(nx) < half and abs(nz) < half:
            b['x'], b['z'] = nx, nz
        else:
            b['hit'] = True
            for _ in range(10):
                spark_list.append(make_spark(b['x'], b['y'], b['z']))

def bullet_alive(b):
    return time.time() - b['born'] < 5 and not b['hit']

def draw_bullet(b):
    glPushMatrix()
    glColor3f(1, 0, 0)
    glTranslatef(b['x'], b['y'], b['z'])
    glutSolidCube(6)
    glPopMatrix()

# --------------------
# ENEMIES
# --------------------
def make_enemy():
    e = respawn_enemy()
    e['marked'] = False
    e['down'] = False
    return e

def respawn_enemy(dummy=None):
    ang = random.uniform(0, 2*math.pi)
    dist = random.uniform(300, 450)
    return {
        'x': dist*math.sin(ang),
        'y': 15,
        'z': dist*math.cos(ang),
        'speed': random.uniform(0.2, 0.5),
        'scale': 1.0,
        'dir': 0.02,
        'born': time.time(),
        'down': False,
        'marked': False
    }

def update_enemy(e):
    dx = hero_position[0] - e['x']
    dz = hero_position[2] - e['z']
    dist = math.sqrt(dx*dx + dz*dz)
    if dist > 0:
        e['x'] += (dx/dist) * e['speed']
        e['z'] += (dz/dist) * e['speed']
    e['scale'] += e['dir']
    if e['scale'] > 1.2 or e['scale'] < 0.8:
        e['dir'] *= -1

def draw_enemy(e):
    if e['down']: return
    glPushMatrix()
    glTranslatef(e['x'], e['y'], e['z'])
    glScalef(e['scale'], e['scale'], e['scale'])
    glColor3f(1,0,0)
    glutSolidSphere(15, 20, 20)
    glPushMatrix()
    glColor3f(0,0,0)
    glTranslatef(0,15,0)
    glutSolidSphere(10,16,16)
    glPopMatrix()
    glPopMatrix()

def enemy_hit_player(e):
    dx = hero_position[0] - e['x']
    dz = hero_position[2] - e['z']
    return math.sqrt(dx*dx + dz*dz) < 30

def enemy_hit_bullet(e, b):
    dx = b['x'] - e['x']
    dz = b['z'] - e['z']
    return math.sqrt(dx*dx + dz*dz) < 15

# --------------------
# PARTICLES
# --------------------
def make_spark(x,y,z):
    return {
        'x':x,'y':y,'z':z,
        'dx':random.uniform(-3,3),
        'dy':random.uniform(0,5),
        'dz':random.uniform(-3,3),
        'life':1.0,
        'col':[1.0, random.uniform(0.5,1.0),0]
    }

def update_spark(p):
    p['x'] += p['dx']
    p['y'] += p['dy']
    p['z'] += p['dz']
    p['dy'] -= 0.2
    p['life'] -= 0.05

def spark_alive(p): return p['life']>0

def draw_spark(p):
    glPushMatrix()
    glColor4f(p['col'][0], p['col'][1], p['col'][2], p['life'])
    glTranslatef(p['x'],p['y'],p['z'])
    glutSolidSphere(2,5,5)
    glPopMatrix()

# --------------------
# HERO DRAWING
# --------------------
def draw_hero():
    glPushMatrix()
    glTranslatef(hero_position[0], hero_position[1], hero_position[2])
    glRotatef(hero_angle,0,1,0)
    if end_flag:
        glRotatef(90,1,0,0)
    glColor3f(0.6,0,1)
    for lx in [7,-7]:
        glPushMatrix()
        glTranslatef(lx,20,0)
        quad = gluNewQuadric()
        gluCylinder(quad,6,3,25,12,6)
        glPopMatrix()
    glColor3f(0.2,0.8,0.2)
    glPushMatrix()
    glTranslatef(0,35,0)
    glScalef(20,30,10)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0,0,0)
    glPushMatrix()
    glTranslatef(0,60,0)
    glutSolidSphere(10,16,16)
    glPopMatrix()
    glColor3f(0.8,0.7,0.6)
    for ax in [-12,12]:
        glPushMatrix()
        glTranslatef(ax,45,0)
        quad = gluNewQuadric()
        gluCylinder(quad,4,2,18,12,2)
        glPopMatrix()
    if not end_flag:
        glColor3f(0.7,0.7,0.7)
        glPushMatrix()
        glTranslatef(0,38,12)
        quad = gluNewQuadric()
        gluCylinder(quad,3.5,2,20,12,2)
        glPopMatrix()
    glPopMatrix()

# --------------------
# FLOOR + WALLS
# --------------------
def draw_floor():
    glDisable(GL_LIGHTING)
    size=50
    for i in range(-10,10):
        for j in range(-10,10):
            if (i+j)%2==0:
                glColor3f(0.8,0.8,0.8)
            else:
                glColor3f(0.3,0.2,0.5)
            x1,z1=i*size,j*size
            x2,z2=(i+1)*size,(j+1)*size
            glBegin(GL_QUADS)
            glVertex3f(x1,-1,z1)
            glVertex3f(x2,-1,z1)
            glVertex3f(x2,-1,z2)
            glVertex3f(x1,-1,z2)
            glEnd()
    half=ARENA_SIZE/2
    wh=70
    glBegin(GL_QUADS)
    glColor3f(1,1,1)
    glVertex3f(-half,-1,-half)
    glVertex3f(half,-1,-half)
    glVertex3f(half,wh,-half)
    glVertex3f(-half,wh,-half)
    glColor3f(0,1,0)
    glVertex3f(half,-1,-half)
    glVertex3f(half,-1,half)
    glVertex3f(half,wh,half)
    glVertex3f(half,wh,-half)
    glColor3f(0,1,1)
    glVertex3f(half,-1,half)
    glVertex3f(-half,-1,half)
    glVertex3f(-half,wh,half)
    glVertex3f(half,wh,half)
    glColor3f(0,0,1)
    glVertex3f(-half,-1,half)
    glVertex3f(-half,-1,-half)
    glVertex3f(-half,wh,-half)
    glVertex3f(-half,wh,half)
    glEnd()
    glEnable(GL_LIGHTING)

# --------------------
# GAME LOOP UPDATE
# --------------------
def update_game():
    global ammo_list, foe_list, spark_list
    global score,lives,missed_shots,end_flag,end_printed
    if end_flag:
        if not end_printed:
            print("Game Over!!")
            end_printed=True
        return
    nb=[]
    for b in ammo_list:
        update_bullet(b)
        if bullet_alive(b):
            nb.append(b)
        else:
            if not b['hit_target']:
                missed_shots+=1
                if missed_shots>=MAX_MISSED: end_flag=True
    ammo_list=nb
    while len(foe_list)<MAX_FOES:
        foe_list.append(make_enemy())
    nf=[]
    for e in foe_list:
        update_enemy(e)
        if enemy_hit_player(e):
            lives-=1
            if lives<=0: end_flag=True
            for _ in range(20):
                spark_list.append(make_spark(e['x'], e['y'], e['z']))
            e=respawn_enemy()
        hit=False
        for b in ammo_list:
            if not b['hit'] and enemy_hit_bullet(e,b):
                b['hit']=True
                b['hit_target']=True
                e['down']=True
                score+=1
                for _ in range(15):
                    spark_list.append(make_spark(e['x'],e['y'],e['z']))
                e=respawn_enemy()
                hit=True
                break
        if not hit: nf.append(e)
    foe_list=nf
    spark_list[:]=[p for p in spark_list if spark_alive(p)]
    for p in spark_list: update_spark(p)

# --------------------
# DRAW STATUS TEXT
# --------------------
def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def draw_status():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0,800,600,0,-1,1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_LIGHTING)
    glColor3f(1, 1, 1)

    draw_text(15, 45, f"Life Left: {lives}")
    draw_text(15, 75, f"Score: {score}")
    draw_text(15, 105, f"Bullets Missed: {missed_shots}")
    draw_text(15, 135, f"Camera: {'First Person' if fp_camera else 'Third Person'}")
    draw_text(15, 165, f"Auto Mode: {'ON' if auto_mode else 'OFF'}")
    if cheat_mode:
        draw_text(15, 195, f"CHEAT MODE ACTIVE!")

    if end_flag:
        draw_text(250, 300, "GAME OVER! Press R to restart")

    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# --------------------
# RENDER
# --------------------
def show():
    glClearColor(0.18,0.18,0.23,1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    set_camera()
    draw_floor()
    if not fp_camera or end_flag:
        draw_hero()
    for b in ammo_list:
        draw_bullet(b)
    for e in foe_list:
        draw_enemy(e)
    for p in spark_list:
        draw_spark(p)
    draw_status()
    glutSwapBuffers()

def set_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 800/600, 1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if fp_camera:
        ex = hero_position[0]
        ey = hero_position[1] + eye_height + 30
        ez = hero_position[2]
        lx = ex + 100 * math.sin(math.radians(hero_angle))
        lz = ez + 100 * math.cos(math.radians(hero_angle))
        gluLookAt(ex, ey, ez, lx, ey, lz, 0, 1, 0)
    else:
        rad = 200
        ex = hero_position[0] + rad * math.sin(math.radians(cam_angle))
        ez = hero_position[2] + rad * math.cos(math.radians(cam_angle))
        ey = hero_position[1] + cam_height
        gluLookAt(ex, ey, ez, hero_position[0], hero_position[1], hero_position[2], 0, 1, 0)

# --------------------
# INPUT
# --------------------
def fire(cheat=False):
    global last_fire_time, hero_angle
    now = time.time()
    if cheat:
        if now - last_fire_time < 0.2:
            return
        bx = hero_position[0]
        by = hero_position[1] + eye_height + 10
        bz = hero_position[2]
        ammo_list.append(make_bullet(bx, by, bz, hero_angle))
        last_fire_time = now
        return

    target = None
    if auto_mode:
        close = None
        md = float('inf')
        for e in foe_list:
            if not e['down'] and not e['marked']:
                dx = e['x'] - hero_position[0]
                dz = e['z'] - hero_position[2]
                d = math.sqrt(dx*dx + dz*dz)
                if d < md:
                    md, close = d, e
        if close:
            target = close
            target['marked'] = True

    if fp_camera:
        bx = hero_position[0]
        by = hero_position[1] + eye_height + 10
        bz = hero_position[2]
        ammo_list.append(make_bullet(bx, by, bz, hero_angle, target))
    else:
        bx = hero_position[0] + 25 * math.sin(math.radians(hero_angle))
        by = hero_position[1] + 35
        bz = hero_position[2] + 25 * math.cos(math.radians(hero_angle))
        ammo_list.append(make_bullet(bx, by, bz, hero_angle, target))

def move_hero(dx, dz):
    nx = hero_position[0] + dx
    nz = hero_position[2] + dz
    half = (ARENA_SIZE / 2) - 30
    if abs(nx) < half and abs(nz) < half:
        hero_position[0], hero_position[2] = nx, nz

def key_press(key, x, y):
    global hero_angle, auto_mode, fp_camera, cheat_mode, auto_gun_follow, end_flag, end_printed
    if end_flag:
        if key == b'r':
            reset()
        return
    if key == b'w':
        move_hero(5 * math.sin(math.radians(hero_angle)), 5 * math.cos(math.radians(hero_angle)))
    elif key == b's':
        move_hero(-5 * math.sin(math.radians(hero_angle)), -5 * math.cos(math.radians(hero_angle)))
    elif key == b'a':
        hero_angle += 5
    elif key == b'd':
        hero_angle -= 5
    elif key == b'c':
        cheat_mode = not cheat_mode
    elif key == b'v':
        auto_gun_follow = not auto_gun_follow
    elif key == b'f':
        fire()

def key_special(k, x, y):
    global cam_angle, cam_height
    if k == GLUT_KEY_LEFT:
        cam_angle -= 1
    elif k == GLUT_KEY_RIGHT:
        cam_angle += 1
    elif k == GLUT_KEY_UP:
        cam_height += 5
    elif k == GLUT_KEY_DOWN:
        cam_height -= 5

def mouse_click(btn, state, x, y):
    global fp_camera
    if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire()
    if btn == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fp_camera = not fp_camera

# --------------------
# RESET + IDLE
# --------------------
def reset():
    global hero_position, hero_angle, ammo_list, foe_list, spark_list
    global auto_mode, fp_camera, cheat_mode, auto_gun_follow
    global score, lives, missed_shots, end_flag, end_printed
    hero_position = [0,0,0]
    hero_angle = 0
    ammo_list.clear()
    foe_list.clear()
    spark_list.clear()
    auto_mode = False
    fp_camera = False
    cheat_mode = False
    auto_gun_follow = False
    score=0
    lives=5
    missed_shots=0
    end_flag=False
    end_printed=False

def idle():
    global hero_angle
    update_game()
    if cheat_mode:
        hero_angle += 5
        if hero_angle >= 360:
            hero_angle -= 360
        fire(cheat=True)
    glutPostRedisplay()

# --------------------
# MAIN
# --------------------
def init():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
glutInitWindowSize(800,600)
glutInitWindowPosition(100,100)
glutCreateWindow(b"3D Shooter Game")
init()
glutDisplayFunc(show)
glutKeyboardFunc(key_press)
glutSpecialFunc(key_special)
glutMouseFunc(mouse_click)
glutIdleFunc(idle)
glutMainLoop()
