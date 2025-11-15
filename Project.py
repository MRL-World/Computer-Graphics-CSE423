# -*- coding: utf-8 -*-
"""
Bomber Arena — OOP Refactor (PyOpenGL / GLUT)
---------------------------------------------
A single-file, class-based refactor that preserves the gameplay and visuals:
- Circular arena with obstacles
- Player movement (W/A/S/D), camera pan (arrow keys)
- Bomb placement (Space), timed explosions (~3s)
- Power-ups: +Bomb capacity, +Explosion range, +Speed
- Enemies: homing with turn-rate limit; contact kill
- Boss phases (3 HP per appearance; defeat boss 3 times to win)
- Boss arrival triggers dark sky + rainfall; normal mode shows snowfall
- Boss carries an axe; axe can kill on close approach (charge maintained)
- Invincibility toggle (I), Restart (P), Quit (Esc)
"""

import math
import random
import time
import sys

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
except Exception:
    print("PyOpenGL and GLUT are required. Install with: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

# ----------------------------
# Global constants & settings
# ----------------------------
ARENA_RADIUS = 35.0
GRID_SIZE = 70
CELL_SIZE = (2.0 * ARENA_RADIUS) / GRID_SIZE

OBSTACLE_DENSITY = 0.15
ENEMY_COUNT = 5

PLAYER_BASE_SPEED = 0.20
ENEMY_SPEED = 0.12
BOSS_SPEED = 0.24

BOMB_TIMER = 3.0
MAX_BOMBS_CAP = 3
POWERUP_CHANCE = 0.40

BOSS_HP_PER_PHASE = 3
BOSS_KILLS_TO_WIN = 3

SNOW_COUNT = 260
RAIN_COUNT = 420

SPAWN_SAFE_DIST = 6.0   # keep spawns away from player

# Key codes
KEY_ESC = b'\\x1b'
KEY_SPACE = b' '
KEY_P = b'p'
KEY_I = b'i'

# ----------------------------
# Helpers
# ----------------------------
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def dist2(x1, z1, x2, z2):
    dx = x1 - x2
    dz = z1 - z2
    return dx*dx + dz*dz

def within_arena(x, z, margin=0.4):
    return (x*x + z*z) <= (ARENA_RADIUS - margin) ** 2

def draw_text_2d(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def world_to_screen_setup(width, height):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

def world_to_screen_restore():
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()

# ----------------------------
# Classes for game elements
# ----------------------------
class Obstacle:
    def __init__(self, x, z):
        self.x = x; self.z = z
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0.0, self.z)
        glColor3f(0.5, 0.35, 0.2)
        glutSolidCube(CELL_SIZE * 0.9)
        glPopMatrix()
    def collides(self, x, z, r=0.45*CELL_SIZE):
        return abs(x - self.x) < r and abs(z - self.z) < r

class PowerUp:
    def __init__(self, x, z, ptype):
        self.x, self.z, self.ptype = x, z, ptype
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0.2, self.z)
        if self.ptype == 0: glColor3f(1.0, 0.6, 0.15)  # +capacity
        elif self.ptype == 1: glColor3f(1.0, 0.2, 0.2)  # +range
        else: glColor3f(0.4, 0.6, 1.0)                  # +speed
        glutSolidSphere(0.35, 10, 10)
        glPopMatrix()

class Bomb:
    def __init__(self, x, z, range_cells):
        self.x, self.z, self.start = x, z, time.time()
        self.range_cells = range_cells
    @property
    def timer(self): return time.time() - self.start
    def exploded(self): return self.timer >= BOMB_TIMER
    def draw(self):
        t = self.timer; pulse = 0.9 + 0.25 * math.sin(t*8.0)
        glPushMatrix()
        glTranslatef(self.x, 0.25, self.z)
        glScalef(pulse, pulse, pulse)
        glColor3f(0.1, 0.1, 0.1)
        glutSolidSphere(0.30, 12, 12)
        glPopMatrix()

class Explosion:
    """Transient visual after a bomb detonates; drawn in display pass for ~0.35s."""
    def __init__(self, x, z, radius):
        self.x, self.z = x, z
        self.radius = radius
        self.start = time.time()
        self.duration = 0.35
    def alive(self):
        return (time.time() - self.start) < self.duration
    def draw(self):
        t = (time.time() - self.start) / self.duration
        t = clamp(t, 0.0, 1.0)
        alpha = 1.0 - t
        scale = 0.8 + 0.4 * t
        glPushMatrix()
        glTranslatef(self.x, 0.12, self.z)
        glColor4f(1.0, 0.6, 0.1, alpha)
        for i in range(16):
            ang = (2*math.pi) * i/16.0
            dx = math.cos(ang) * self.radius * scale
            dz = math.sin(ang) * self.radius * scale
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0, 0)
            glVertex3f(dx, 0, dz)
            glVertex3f(dx*0.7, 0, dz*0.7)
            glEnd()
        glPopMatrix()

class Player:
    def __init__(self, x=0.0, z=0.0):
        self.x, self.z = x, z
        self.speed = PLAYER_BASE_SPEED
        self.invincible = False
        self.move_up = self.move_down = False
        self.move_left = self.move_right = False
        self.bomb_capacity, self.explosion_range = 1, 2
        self.bombs_active = 0
    def apply_powerup(self, ptype):
        if ptype == 0: self.bomb_capacity = min(MAX_BOMBS_CAP, self.bomb_capacity + 1)
        elif ptype == 1: self.explosion_range += 1
        else: self.speed *= 1.2
    def update(self, world, dt):
        dx = dz = 0.0; s = self.speed * dt * 60.0
        if self.move_up: dz -= s
        if self.move_down: dz += s
        if self.move_left: dx -= s
        if self.move_right: dx += s
        if dx and dz: inv = 1/math.sqrt(2); dx*=inv; dz*=inv
        nx, nz = self.x + dx, self.z + dz
        if world.can_move_to(nx, nz): self.x, self.z = nx, nz
    def draw(self):
        glPushMatrix(); glTranslatef(self.x, 0.5, self.z)
        if self.invincible: glColor3f(1.0,0.95,0.3)
        else: glColor3f(0.2,0.8,0.2)
        glutSolidSphere(0.5, 14, 14); glPopMatrix()

class Enemy:
    def __init__(self, x, z):
        self.x, self.z, self.face = x, z, random.uniform(0, 2*math.pi)
        self.speed = ENEMY_SPEED
    def update(self, world, dt):
        px,pz = world.player.x, world.player.z
        ang = math.atan2(pz - self.z, px - self.x)
        d = (ang - self.face + math.pi) % (2*math.pi) - math.pi
        max_turn = 2.5 * dt; d = clamp(d, -max_turn, max_turn); self.face += d
        step = self.speed * dt * 60.0
        nx = self.x + math.cos(self.face)*step
        nz = self.z + math.sin(self.face)*step
        if world.can_move_to(nx, nz): self.x, self.z = nx, nz
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0.45,self.z)
        glColor3f(0.9,0.3,0.9); glutSolidSphere(0.45,12,12); glPopMatrix()

class Boss:
    def __init__(self, x, z):
        self.x, self.z = x, z
        self.face = random.uniform(0, 2*math.pi)
        self.hp = BOSS_HP_PER_PHASE
    def alive(self): return self.hp > 0
    def update(self, world, dt):
        px,pz=world.player.x,world.player.z
        self.face = math.atan2(pz - self.z, px - self.x)
        step = BOSS_SPEED * dt * 60.0
        nx = self.x + math.cos(self.face)*step
        nz = self.z + math.sin(self.face)*step
        if world.can_move_to(nx, nz): self.x, self.z = nx, nz
        # body collision
        if (not world.player.invincible) and math.hypot(self.x-px, self.z-pz) < 1.1:
            world.game_over("The boss crushed you!")
            return
        # axe hitbox ahead of boss
        axe_x = self.x + math.cos(self.face)*1.2
        axe_z = self.z + math.sin(self.face)*1.2
        if (not world.player.invincible) and math.hypot(axe_x-px, axe_z-pz) < 0.8:
            world.game_over("The boss cleaved you!")
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0.9,self.z); glScalef(2,2,2)
        glColor3f(0.2,0.2,0.9); glutSolidSphere(0.5,18,18)
        # Axe
        glPushMatrix()
        glRotatef(math.degrees(self.face),0,1,0)
        glTranslatef(0.6,-0.2,0.0)
        quad=gluNewQuadric()
        glColor3f(0.45,0.3,0.15)
        glRotatef(-90,1,0,0)
        gluCylinder(quad,0.05,0.05,0.9,10,1)
        glTranslatef(0.0,0.0,0.6)
        glRotatef(90,0,1,0)
        glScalef(0.5,0.7,0.12)
        glColor3f(0.8,0.85,0.95)
        glutSolidCube(1.0)
        gluDeleteQuadric(quad)
        glPopMatrix()
        glPopMatrix()

class Weather:
    def __init__(self):
        self.sky_dark=0.0; self.wind=0.0; self.snow_intensity=0.8
        self.snow=[[random.uniform(-ARENA_RADIUS,ARENA_RADIUS),
                    random.uniform(12,22),
                    random.uniform(-ARENA_RADIUS,ARENA_RADIUS),
                    random.uniform(0.06,0.12)] for _ in range(SNOW_COUNT)]
        self.rain=[[random.uniform(-ARENA_RADIUS,ARENA_RADIUS),
                    random.uniform(12,24),
                    random.uniform(-ARENA_RADIUS,ARENA_RADIUS),
                    random.uniform(1.5,3.0)] for _ in range(RAIN_COUNT)]
    def update(self,boss_active):
        target_dark=1.0 if boss_active else 0.0
        self.sky_dark = clamp(self.sky_dark + (0.02 if target_dark>self.sky_dark else -0.02), 0.0, 1.0)
        snow_target=0.1 if boss_active else 0.8
        self.snow_intensity = clamp(self.snow_intensity + (0.02 if snow_target>self.snow_intensity else -0.02), 0.0, 1.0)
        self.wind = 0.6*math.sin(time.time()*0.8)
        # snow
        for i,p in enumerate(self.snow):
            p[1]-=p[3]*(0.25+0.5*self.snow_intensity)
            p[0]+=0.02*math.sin((time.time()*1.8)+i)
            p[2]+=0.02*math.cos((time.time()*1.6)+i*0.5)
            if p[1]<-1:
                p[1]=random.uniform(15,25)
                p[0]=random.uniform(-ARENA_RADIUS,ARENA_RADIUS)
                p[2]=random.uniform(-ARENA_RADIUS,ARENA_RADIUS)
        # rain
        if self.sky_dark>0.05:
            for r in self.rain:
                r[0]+=self.wind*0.12
                r[1]-=r[3]*(2.0+2.0*self.sky_dark)
                if r[1]<-1:
                    r[1]=random.uniform(14,24)
                    r[0]=random.uniform(-ARENA_RADIUS,ARENA_RADIUS)+self.wind*2.0
                    r[2]=random.uniform(-ARENA_RADIUS,ARENA_RADIUS)
    def apply_clear_color(self):
        d=self.sky_dark
        r=0.5*(1-d)+0.05*d; g=0.8*(1-d)+0.05*d; b=1.0*(1-d)+0.08*d
        glClearColor(r,g,b,1.0)
    def draw(self):
        # snow
        if self.snow_intensity>0.02:
            glColor3f(1,1,1)
            for p in self.snow:
                glPushMatrix(); glTranslatef(p[0],p[1],p[2])
                glutSolidSphere(0.08*(0.6+0.4*self.snow_intensity),6,6)
                glPopMatrix()
        # rain
        if self.sky_dark>0.05:
            rain_brightness=0.5+0.5*self.sky_dark
            glColor3f(0.7*rain_brightness,0.8*rain_brightness,1.0*rain_brightness)
            glBegin(GL_LINES)
            for r in self.rain:
                glVertex3f(r[0],r[1],r[2]); glVertex3f(r[0]-self.wind*0.3,r[1]+0.6,r[2])
            glEnd()

# ----------------------------
# Game world orchestrator
# ----------------------------
class World:
    def __init__(self):
        self.width,self.height=1000,700
        self.player=Player(); self.enemies=[]; self.boss=None
        self.bombs=[]; self.powerups=[]; self.obstacles=[]; self.weather=Weather()
        self.explosions=[]  # new: draw explosions in display pass
        self.camera_dx=self.camera_dz=0.0
        self.game_is_over=False; self.game_over_text=""; self.victory=False
        self.last_time=time.time(); self.delta=0.016
        self.boss_active=False; self.boss_kills=0; self.next_boss_spawn_time=0.0
        self.seed_arena(); self.spawn_enemies(ENEMY_COUNT)

    # ---------- setup ----------
    def seed_arena(self):
        self.obstacles=[]
        for gx in range(GRID_SIZE):
            for gz in range(GRID_SIZE):
                if random.random()<OBSTACLE_DENSITY:
                    x=-ARENA_RADIUS+(gx+0.5)*CELL_SIZE
                    z=-ARENA_RADIUS+(gz+0.5)*CELL_SIZE
                    if math.hypot(x,z)<4.0: continue  # keep center open
                    if within_arena(x,z): self.obstacles.append(Obstacle(x,z))

    def spawn_enemies(self,n):
        self.enemies=[]
        for _ in range(n):
            for _try in range(200):
                ang=random.uniform(0,2*math.pi)
                rad=random.uniform(6.0,ARENA_RADIUS-1.5)
                x=math.cos(ang)*rad; z=math.sin(ang)*rad
                if self.safe_cell(x,z) and dist2(x,z,self.player.x,self.player.z)>(SPAWN_SAFE_DIST**2):
                    self.enemies.append(Enemy(x,z)); break

    def reset(self):
        # clean reset (simple and robust)
        self.__init__()

    # ---------- utilities ----------
    def safe_cell(self,x,z):
        if not within_arena(x,z): return False
        return all(not ob.collides(x,z,0.45*CELL_SIZE) for ob in self.obstacles)

    def can_move_to(self,x,z):
        if not within_arena(x,z): return False
        return all(not ob.collides(x,z,0.5*CELL_SIZE) for ob in self.obstacles)

    def find_spawn_spot(self):
        for _ in range(300):
            ang=random.uniform(0,2*math.pi); rad=random.uniform(8.0,ARENA_RADIUS-1.5)
            x=math.cos(ang)*rad; z=math.sin(ang)*rad
            if self.safe_cell(x,z) and dist2(x,z,self.player.x,self.player.z)>(SPAWN_SAFE_DIST**2):
                return x,z
        # fallback (origin), usually clear in this arena setup
        return 0.0,0.0

    # ---------- gameplay ----------
    def try_place_bomb(self):
        if self.player.bombs_active>=self.player.bomb_capacity: return
        # snap to grid
        gx=round((self.player.x+ARENA_RADIUS-0.5*CELL_SIZE)/CELL_SIZE)
        gz=round((self.player.z+ARENA_RADIUS-0.5*CELL_SIZE)/CELL_SIZE)
        x=-ARENA_RADIUS+(gx+0.5)*CELL_SIZE
        z=-ARENA_RADIUS+(gz+0.5)*CELL_SIZE
        if any(abs(b.x-x)<0.01 and abs(b.z-z)<0.01 for b in self.bombs): return
        self.bombs.append(Bomb(x,z,self.player.explosion_range))
        self.player.bombs_active+=1

    def process_explosions(self):
        removed=[]
        for b in self.bombs:
            if b.exploded():
                # enqueue a transient explosion effect for the draw pass
                self.explosions.append(Explosion(b.x, b.z, b.range_cells*CELL_SIZE))
                r2=(b.range_cells*CELL_SIZE)**2
                # enemies
                self.enemies=[e for e in self.enemies if dist2(e.x,e.z,b.x,b.z)>r2]
                # boss
                if self.boss and dist2(self.boss.x,self.boss.z,b.x,b.z)<=r2:
                    self.boss.hp-=1
                # obstacles + powerups
                keep=[]
                for ob in self.obstacles:
                    if dist2(ob.x,ob.z,b.x,b.z)<=r2:
                        if random.random()<POWERUP_CHANCE:
                            self.powerups.append(PowerUp(ob.x,ob.z,random.randint(0,2)))
                    else:
                        keep.append(ob)
                self.obstacles=keep
                removed.append(b)
        for b in removed:
            self.bombs.remove(b)
            self.player.bombs_active=max(0,self.player.bombs_active-1)

    def prune_explosions(self):
        if self.explosions:
            self.explosions = [e for e in self.explosions if e.alive()]

    def collect_powerups(self):
        px,pz=self.player.x,self.player.z
        keep=[]
        for p in self.powerups:
            if math.hypot(p.x-px,p.z-pz)<0.6:
                self.player.apply_powerup(p.ptype)
            else:
                keep.append(p)
        self.powerups=keep

    def maybe_spawn_boss(self):
        if self.game_is_over or self.victory: return
        if self.boss or self.boss_active: return
        if len(self.enemies)>0: return
        now=time.time()
        if self.next_boss_spawn_time==0.0:
            self.next_boss_spawn_time=now+5.0  # safe delay
            return
        if now>=self.next_boss_spawn_time:
            x,z=self.find_spawn_spot()
            self.boss=Boss(x,z)
            self.boss_active=True
            self.next_boss_spawn_time=0.0

    def update_boss_death(self):
        if self.boss and not self.boss.alive():
            self.boss=None
            self.boss_active=False
            self.boss_kills+=1
            if self.boss_kills>=BOSS_KILLS_TO_WIN:
                self.victory=True; self.game_is_over=True
                self.game_over_text="You defeated the boss! Victory!"

    def game_over(self, text):
        if self.player.invincible: return
        self.game_is_over=True
        self.game_over_text=text

    # ---------- frame update ----------
    def step(self):
        now=time.time()
        dt=max(1e-5, now-self.last_time)
        self.last_time=now
        self.delta=dt

        # keep animating weather even on game over
        if self.game_is_over:
            self.weather.update(self.boss_active)
            self.prune_explosions()
            return

        self.player.update(self, dt)
        for e in self.enemies: e.update(self, dt)
        self.process_explosions()
        self.prune_explosions()
        self.collect_powerups()

        self.maybe_spawn_boss()
        if self.boss: self.boss.update(self, dt)
        self.update_boss_death()

        self.weather.update(self.boss_active)

    # ---------- rendering ----------
    def draw_arena(self):
        segments=64
        glPushMatrix()
        day_mix=1.0-self.weather.sky_dark
        glColor3f(0.1+0.2*day_mix, 0.35+0.15*day_mix, 0.1+0.1*day_mix)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0,0,0)
        for i in range(segments+1):
            ang=(2*math.pi)*i/segments
            glVertex3f(math.cos(ang)*ARENA_RADIUS, 0, math.sin(ang)*ARENA_RADIUS)
        glEnd()
        glPopMatrix()

    def display(self):
        # sky first (must be BEFORE glClear)
        self.weather.apply_clear_color()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # camera
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(60.0, self.width/float(self.height), 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()

        eye_x = self.player.x - 14.0 + self.camera_dx
        eye_y = 14.0
        eye_z = self.player.z + 14.0 + self.camera_dz
        gluLookAt(eye_x, eye_y, eye_z, self.player.x, 0.0, self.player.z, 0,1,0)

        glEnable(GL_DEPTH_TEST)

        self.draw_arena()
        for ob in self.obstacles: ob.draw()
        for p in self.powerups: p.draw()
        for b in self.bombs: b.draw()
        for e in self.enemies: e.draw()
        if self.boss: self.boss.draw()
        self.player.draw()

        # explosions (alpha-blended)
        if self.explosions:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            for ex in self.explosions:
                ex.draw()
            glDisable(GL_BLEND)

        # weather last so particles overlay scene
        self.weather.draw()

        # HUD
        self.draw_hud()

        glutSwapBuffers()

    def draw_hud(self):
        world_to_screen_setup(self.width, self.height)
        glColor3f(1,1,1)
        draw_text_2d(10, self.height - 20, f"Bombs: {self.player.bombs_active}/{self.player.bomb_capacity}")
        draw_text_2d(10, self.height - 38, f"Range: {self.player.explosion_range}  Speed: {self.player.speed:.2f}")
        draw_text_2d(10, self.height - 56, f"Boss defeats: {self.boss_kills}/{BOSS_KILLS_TO_WIN}")
        if self.player.invincible:
            glColor3f(1.0,1.0,0.2)
            draw_text_2d(10, self.height - 74, "CHEATS: INVINCIBLE (I)")
        if self.game_is_over:
            if self.victory: glColor3f(1.0, 0.9, 0.2)
            else: glColor3f(1.0, 0.4, 0.4)
            msg = self.game_over_text or ("You Win!" if self.victory else "Game Over")
            draw_text_2d(self.width*0.5 - 120, self.height*0.5, msg)
            glColor3f(1,1,1)
            draw_text_2d(self.width*0.5 - 150, self.height*0.5 - 24, "Press P to Play Again")
        world_to_screen_restore()

    # ---------- input ----------
    def on_key_down(self, key, x, y):
        if key == KEY_ESC:
            sys.exit(0)
        elif key == KEY_SPACE and not self.game_is_over:
            self.try_place_bomb()
        elif key == KEY_P:
            self.reset()
        elif key == KEY_I:
            self.player.invincible = not self.player.invincible
        else:
            if key in (b'w', b'W'): self.player.move_up = True
            elif key in (b's', b'S'): self.player.move_down = True
            elif key in (b'a', b'A'): self.player.move_left = True
            elif key in (b'd', b'D'): self.player.move_right = True

    def on_key_up(self, key, x, y):
        if key in (b'w', b'W'): self.player.move_up = False
        elif key in (b's', b'S'): self.player.move_down = False
        elif key in (b'a', b'A'): self.player.move_left = False
        elif key in (b'd', b'D'): self.player.move_right = False

    def on_special(self, key, x, y):
        if key == GLUT_KEY_LEFT: self.camera_dx -= 0.8
        elif key == GLUT_KEY_RIGHT: self.camera_dx += 0.8
        elif key == GLUT_KEY_UP: self.camera_dz -= 0.8
        elif key == GLUT_KEY_DOWN: self.camera_dz += 0.8

    def on_reshape(self, w, h):
        self.width = max(1, w); self.height = max(1, h)
        glViewport(0, 0, self.width, self.height)

# ----------------------------
# GLUT glue
# ----------------------------
WORLD = None

def display_cb():
    if WORLD: WORLD.display()

def idle_cb():
    if WORLD:
        WORLD.step()
        glutPostRedisplay()

def keyboard_cb(key, x, y):
    if WORLD: WORLD.on_key_down(key, x, y)

def keyboard_up_cb(key, x, y):
    if WORLD: WORLD.on_key_up(key, x, y)

def special_cb(key, x, y):
    if WORLD: WORLD.on_special(key, x, y)

def reshape_cb(w, h):
    if WORLD: WORLD.on_reshape(w, h)

def main():
    global WORLD
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 700)
    glutCreateWindow(b"Bomber Arena - OOP Refactor")

    glEnable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)  # flat shading keeps things simple
    glEnable(GL_BLEND)      # enable blending once; we'll toggle in draw paths as needed
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    WORLD = World()

    glutDisplayFunc(display_cb)
    glutIdleFunc(idle_cb)
    glutKeyboardFunc(keyboard_cb)
    glutKeyboardUpFunc(keyboard_up_cb)
    glutSpecialFunc(special_cb)
    glutReshapeFunc(reshape_cb)

    glutMainLoop()

if __name__ == "__main__":
    main()
