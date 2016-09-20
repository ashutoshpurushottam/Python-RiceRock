# Implementation
import simplegui
import math
import random

# globals for user interface
WIDTH = 800
HEIGHT = 600
DIMENSION = [WIDTH, HEIGHT]
score = 0
lives = 3
time = 0.5
started = False

# constants for user interface
TEXT_SIZE = 40
NUMBER_SIZE = 30
FONT = "sans-serif"
SIDE_OFF_SET = 100
TOP_OFF_SET = 50
FONT_COLOUR = "aqua"

# for ship
SHIP_INIT_VEL = [0, 0]
ANG_ACCN = 0.2
ACC_FRAC = 0.3
FRIC_FRAC = 0.01
# for rock
ROCK_INIT_VEL = [1, 1]
ROCK_INIT_ANG = 1
ROCK_ANG_VEL = 0.05
ROCK_FAC = 0.1
ROCK_ANG_FAC = 0.01

# for missile
MISSILE_FAC = 2
MISSILE_SPEED_MINIMUM = 3

# for rock in project 2
rock_group = set([])
# for missiles in proj 2
missile_group = set([])
num_of_collision = 0
# factor of ship and spawning rock
MIN_DIS_FAC = 1.2

# for explosion
explosion_group = set([])


class ImageInfo:

    def __init__(self, center, size, radius=0, lifespan=None, animated=False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated


# art assets created by Kim Lathrop, may be freely re-used in
# non-commercial projects, please credit Kim

debris_info = ImageInfo([320, 240], [640, 480])
debris_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/debris2_blue.png")

# nebula images - nebula_brown.png, nebula_blue.png
nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/nebula_blue.s2014.png")

# splash image
splash_info = ImageInfo([200, 150], [400, 300])
splash_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/splash.png")

# ship image
ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/double_ship.png")

# missile image - shot1.png, shot2.png, shot3.png
missile_info = ImageInfo([5, 5], [10, 10], 3, 50)
missile_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/shot2.png")

# asteroid images - asteroid_blue.png, asteroid_brown.png, asteroid_blend.png
asteroid_info = ImageInfo([45, 45], [90, 90], 40)
asteroid_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/asteroid_blue.png")

# animated explosion - explosion_orange.png, explosion_blue.png,
# explosion_blue2.png, explosion_alpha.png
explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
explosion_image = simplegui.load_image(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/explosion_alpha.png")

# sound assets purchased from sounddogs.com, please do not redistribute
soundtrack = simplegui.load_sound(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/soundtrack.mp3")
missile_sound = simplegui.load_sound(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/missile.mp3")
missile_sound.set_volume(.5)
ship_thrust_sound = simplegui.load_sound(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/thrust.mp3")
explosion_sound = simplegui.load_sound(
    "http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/explosion.mp3")

# helper functions to handle transformations


def angle_to_vector(ang):
    return [math.cos(ang), math.sin(ang)]


def dist(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

# some more helper functions

# random number generator helper function


def ran():
    return random.randrange(-20, 20)

# process the sets of item


def process_sprite_group(sets, canvas):

    copy_set = set(sets)
    for item in copy_set:
        if item.update():
            sets.discard(item)

    for objs in sets:
        objs.draw(canvas)


# remove rocks that got collided with ship
def group_collide(sets, sprite):
    global explosion_group

    collision = False
    set_copy = set(sets)
    for item in set_copy:
        if item.collide(sprite):
            sets.remove(item)
            explosion = Sprite(
                sprite.pos,
                sprite.vel,
                sprite.angle,
                sprite.angle_vel,
                explosion_image,
                explosion_info)
            explosion_group.add(explosion)
            collision = True
            explosion_sound.play()
    return collision

# remove rocks that got collided with missiles


def group_group_collide(set1, set2):
    global num_of_collision
    set1_copy = set(set1)
    for item in set1_copy:
        if group_collide(set2, item):
            set1.remove(item)
            num_of_collision += 1
    return num_of_collision


# Ship class
class Ship:

    def __init__(self, pos, vel, angle, image, info):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = angle
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.forward_vec = angle_to_vector(self.angle)
        self.resultant_vel = math.sqrt(self.vel[0]**2 + self.vel[1]**2)

    def get_pos(self):
        return self.pos

    def get_rad(self):
        return self.radius

    def draw(self, canvas):
        # spaceship image when thrusting
        if self.thrust:
            canvas.draw_image(self.image,
                              [self.image_center[0] + self.image_size[0],
                               self.image_center[0]],
                              self.image_size,
                              self.pos,
                              self.image_size,
                              self.angle)
        # spaceship image when not thrusting
        else:
            canvas.draw_image(
                self.image,
                self.image_center,
                self.image_size,
                self.pos,
                self.image_size,
                self.angle)

    def update(self):

        # add some friction to the ship

        for i in range(2):
            self.vel[i] *= (1 - FRIC_FRAC)

        # updating position with respect to velocity
        for i in range(2):
            self.pos[i] = (self.pos[i] + self.vel[i]) % DIMENSION[i]

        # updating angle with respect to angular velocity
        self.angle += self.angle_vel
        # calculating forward vector given the ship's angle

        self.forward_vec = angle_to_vector(self.angle)

        self.resultant_vel = math.sqrt(self.vel[0]**2 + self.vel[1]**2)

        # accelerates ship if thrusting
        if self.thrust:
            for i in range(2):
                self.vel[i] += ACC_FRAC * self.forward_vec[i]

    # action taken when spaceship is thrusting/not thrusting

    def is_thrusting(self, thrusting):

        if thrusting:
            self.thrust = True
            ship_thrust_sound.play()
        else:
            self.thrust = False
            ship_thrust_sound.rewind()

    # method for shooting

    def shoot(self):
        global missile_group
        # missile position
        missilePos_x = self.pos[
            0] + my_ship.image_size[0] / 2.0 * math.cos(self.angle)
        missilePos_y = self.pos[
            1] + my_ship.image_size[0] / 2.0 * math.sin(self.angle)
        missilePos = [missilePos_x, missilePos_y]
        # missile velocity
        missileVel = [0, 0]
        for i in range(2):
            missileVel[i] = (
                MISSILE_SPEED_MINIMUM + self.resultant_vel) * MISSILE_FAC * self.forward_vec[i]
        # create a missile object
        missile = Sprite(
            missilePos,
            missileVel,
            0,
            0,
            missile_image,
            missile_info,
            missile_sound)
        missile_group.add(missile)

# Sprite class


class Sprite:

    def __init__(self, pos, vel, ang, ang_vel, image, info, sound=None):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound:
            sound.rewind()
            sound.play()

    def get_pos(self):
        return self.pos

    def get_rad(self):
        return self.radius

    def draw(self, canvas):
        # determine which tile should be drawn currently
        current_image_index = (self.age % 24) // 1
        # determine the center of that tile
        current_center = [
            (self.image_center[0] +
             current_image_index *
             self.image_size[0]),
            self.image_center[1]]
        # draw animation if explosion occurs
        if self.animated:
            canvas.draw_image(
                self.image,
                current_center,
                self.image_size,
                self.pos,
                self.image_size,
                self.angle)
        else:
            # draw image of rock
            canvas.draw_image(
                self.image,
                self.image_center,
                self.image_size,
                self.pos,
                self.image_size,
                self.angle)

    def update(self):

        # updating the angular pos
        self.angle += self.angle_vel
        self.age += 1

        # updating the translational motion of rock
        for i in range(2):
            self.pos[i] = (self.pos[i] + self.vel[i]) % DIMENSION[i]

        if self.age >= self.lifespan:
            return True
        else:
            return False

    # method for colliding object
    def collide(self, other_object):

        # check if the objects are colliding
        if dist(self.get_pos(), other_object.get_pos()
                ) < self.get_rad() + other_object.get_rad():
            return True
        else:
            return False


def draw(canvas):
    global time, lives, score, started

    # animiate background
    time += 1
    wtime = (time / 4) % WIDTH
    center = debris_info.get_center()
    size = debris_info.get_size()
    canvas.draw_image(nebula_image, nebula_info.get_center(
    ), nebula_info.get_size(), [WIDTH / 2, HEIGHT / 2], [WIDTH, HEIGHT])
    canvas.draw_image(debris_image, center, size,
                      (wtime - WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT))
    canvas.draw_image(debris_image, center, size,
                      (wtime + WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT))

    # draw ship and sprites
    my_ship.draw(canvas)

    # drawing each rock to the canvas
    if started:
        process_sprite_group(rock_group, canvas)

    # drawing each missile to the canvas
    process_sprite_group(missile_group, canvas)

    # drawing each explosion
    process_sprite_group(explosion_group, canvas)

    # update ship and sprites
    my_ship.update()

    # draw lives and score for user
    # getting text width
    lives_length = frame.get_canvas_textwidth("Lives", TEXT_SIZE, FONT)
    score_length = frame.get_canvas_textwidth("Score", TEXT_SIZE, FONT)
    number_length = frame.get_canvas_textwidth(str(lives), NUMBER_SIZE, FONT)

    # draw the text
    canvas.draw_text(
        "Lives", [
            SIDE_OFF_SET, TOP_OFF_SET], TEXT_SIZE, FONT_COLOUR, FONT)
    canvas.draw_text("Score",
                     [WIDTH - (SIDE_OFF_SET + score_length),
                      TOP_OFF_SET],
                     TEXT_SIZE,
                     FONT_COLOUR,
                     FONT)

    # draw numbers
    canvas.draw_text(str(lives),
                     [SIDE_OFF_SET + lives_length / 2 - number_length / 2,
                      TOP_OFF_SET + TEXT_SIZE],
                     NUMBER_SIZE,
                     FONT_COLOUR,
                     FONT)
    canvas.draw_text(str(score), [WIDTH -
                                  SIDE_OFF_SET -
                                  score_length /
                                  2 -
                                  number_length /
                                  2, TOP_OFF_SET +
                                  TEXT_SIZE], NUMBER_SIZE, FONT_COLOUR, FONT)

    # draw splash screen if not started
    if not started or lives < 1:
        canvas.draw_image(splash_image, splash_info.get_center(),
                          splash_info.get_size(), [WIDTH / 2, HEIGHT / 2],
                          splash_info.get_size())
        started = False

    # decrease live if rock-ship collide
    if group_collide(rock_group, my_ship)and started:
        lives -= 1
    # increment score when missiles and rocks collide
    group_group_collide(rock_group, missile_group)
    if started:
        score = num_of_collision


# timer handler that spawns a rock
def rock_spawner():
    global time, rock_group
    # random position for rock
    ran_pos = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]
    # random velociy for rock
    ran_vel = [ROCK_FAC * ran() * (score + ROCK_INIT_VEL[0]),
               ROCK_FAC * ran() * (score + ROCK_INIT_VEL[0])]
    # random angular velocity for rock
    ran_ang_vel = ROCK_ANG_FAC * ran()

    # limiting number of rocks to twelve
    if started:

        # creating rock
        rock = Sprite(
            ran_pos,
            ran_vel,
            1,
            ran_ang_vel,
            asteroid_image,
            asteroid_info)
        if len(rock_group) < 12 and dist(my_ship.pos,
                                         ran_pos) > MIN_DIS_FAC * (my_ship.get_rad() + rock.get_rad()):
            rock_group.add(rock)

    time += 1


# key down handlers

def keydown(key):
    if key == simplegui.KEY_MAP["left"]:
        my_ship.angle_vel -= ANG_ACCN

    elif key == simplegui.KEY_MAP["right"]:
        my_ship.angle_vel += ANG_ACCN

    elif key == simplegui.KEY_MAP["up"]:
        my_ship.is_thrusting(True)

    elif key == simplegui.KEY_MAP["space"]:
        my_ship.shoot()

# key up handlers


def keyup(key):
    my_ship.angle_vel = 0
    my_ship.is_thrusting(False)

# mouseclick handlers that reset UI and conditions whether splash image is
# drawn


def click(pos):
    global started, lives, num_of_collision, rock_group
    center = [WIDTH / 2, HEIGHT / 2]
    size = splash_info.get_size()
    inwidth = (center[0] - size[0] / 2) < pos[0] < (center[0] + size[0] / 2)
    inheight = (center[1] - size[1] / 2) < pos[1] < (center[1] + size[1] / 2)
    if (not started) and inwidth and inheight:
        rock_group = set([])
        lives = 3
        num_of_collision = 0
        started = True
    soundtrack.play()


# initialize frame
frame = simplegui.create_frame("Asteroids", WIDTH, HEIGHT)

# initialize ship and two sprites
my_ship = Ship([WIDTH / 2, HEIGHT / 2], SHIP_INIT_VEL,
               0, ship_image, ship_info)

# register handlers
frame.set_draw_handler(draw)
frame.set_keydown_handler(keydown)
frame.set_keyup_handler(keyup)
frame.set_mouseclick_handler(click)

timer = simplegui.create_timer(1000.0, rock_spawner)

# get things rolling
timer.start()
frame.start()
