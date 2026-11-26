"""
MU Fireworks Simulator v0.2 — Grand Show Update
A visual-only 2D particle simulation. No real-world firework construction
or launch instructions.

Install: py -m pip install pygame-ce
Run:     py mu_fireworks.py

CONTROLS
  Left click  Launch toward cursor
  SPACE       Launch a random shell
  1-8         Select a firework style
  0           Random firework style
  B           Toggle black sky / backyard
  R           Toggle automatic show
  P           Pause / resume
  +/-         Simulation speed
  H           Toggle HUD
  F           Toggle fullscreen
  C           Clear sky
  ESC         Quit
"""

import math
import random
import sys
import array
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 1280, 720
FPS = 60
MAX_PARTICLES = 12500
GRAVITY = 118.0
TAU = math.tau

PALETTES = [
    [(255, 196, 92), (255, 238, 190), (255, 130, 65)],
    [(255, 65, 76), (255, 180, 105), (255, 235, 205)],
    [(80, 165, 255), (160, 220, 255), (245, 250, 255)],
    [(115, 255, 155), (220, 255, 150), (255, 240, 170)],
    [(190, 105, 255), (255, 155, 220), (255, 230, 250)],
    [(255, 245, 205), (255, 255, 255), (255, 180, 80)],
    [(255, 90, 190), (130, 120, 255), (255, 220, 245)],
    [(255, 225, 70), (255, 150, 35), (255, 250, 190)],
]
EFFECTS = [
    "Peony", "Chrysanthemum", "Willow", "Ring",
    "Palm", "Crackle", "Strobe", "Brocade"
]


def clamp(value, low, high):
    return max(low, min(high, value))


def mix_color(a, b, amount):
    amount = clamp(amount, 0.0, 1.0)
    return tuple(round(a[i] + (b[i] - a[i]) * amount) for i in range(3))


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: tuple
    life: float
    max_life: float
    drag: float = 0.985
    gravity: float = GRAVITY
    glow: bool = True
    flicker: float = 0.0
    smoke: bool = False
    split: bool = False
    split_done: bool = False

    def update(self, dt, children):
        self.life -= dt
        if self.life <= 0:
            return False
        factor = self.drag ** (dt * 60.0)
        self.vx *= factor
        self.vy *= factor
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.split and not self.split_done and self.life <= self.max_life * 0.48:
            self.split_done = True
            for _ in range(3):
                angle = random.uniform(0, TAU)
                speed = random.uniform(35, 95)
                children.append(Particle(
                    self.x, self.y, math.cos(angle) * speed,
                    math.sin(angle) * speed, random.uniform(1.0, 1.8),
                    mix_color(self.color, (255, 245, 210), random.random() * 0.35),
                    random.uniform(0.25, 0.5), 0.5, drag=0.975,
                    glow=True, flicker=0.12
                ))
        return True

    def draw(self, surface, glow_surface):
        remaining = clamp(self.life / self.max_life, 0.0, 1.0)
        if self.smoke:
            alpha = int(65 * (1.0 - remaining) * min(1.0, self.life * 1.5))
            radius = max(2, int(self.radius * (1.0 + (1.0 - remaining) * 2.2)))
            color = tuple(int(c * 0.35) for c in self.color)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), radius)
            return

        alpha = int(255 * (remaining ** 0.68))
        if self.flicker and random.random() < self.flicker:
            alpha = int(alpha * random.uniform(0.12, 0.62))
        x, y = int(self.x), int(self.y)
        radius = max(1, int(self.radius * (0.55 + remaining * 0.45)))
        core = tuple(int(c * alpha / 255) for c in self.color)

        if self.glow and radius >= 1:
            glow_color = tuple(int(c * 0.12 * alpha / 255) for c in self.color)
            pygame.draw.circle(glow_surface, glow_color, (x, y), radius * 4)
        pygame.draw.circle(surface, core, (x, y), radius)


@dataclass
class Rocket:
    x: float
    y: float
    vx: float
    vy: float
    hue: tuple
    effect: int
    age: float = 0.0
    fuse: float = 0.9
    trail_clock: float = 0.0
    trail_color: tuple = (255, 220, 155)

    def update(self, dt, particles):
        self.age += dt
        self.trail_clock += dt
        self.vx += random.uniform(-5.5, 5.5) * dt
        self.vy += 24.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        while self.trail_clock >= 0.014:
            self.trail_clock -= 0.014
            if len(particles) < MAX_PARTICLES - 2:
                particles.append(Particle(
                    self.x + random.uniform(-1.5, 1.5),
                    self.y + random.uniform(-1.5, 1.5),
                    -self.vx * 0.07 + random.uniform(-15, 15),
                    -self.vy * 0.06 + random.uniform(-15, 15),
                    random.uniform(1.1, 2.4),
                    random.choice([self.trail_color, (255, 245, 215), self.hue]),
                    random.uniform(0.22, 0.48), 0.48,
                    drag=0.93, flicker=0.12
                ))
        return self.age >= self.fuse or self.y < 58


class SoundEngine:
    """Procedural game audio synthesized at runtime."""
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(12)
            self.sounds = {name: self._build(name) for name in ("launch", "burst", "crackle", "firecracker", "fountain")}
        except pygame.error:
            self.enabled, self.sounds = False, {}

    def _build(self, kind):
        rate = 22050
        duration = {"launch": .42, "burst": .55, "crackle": .24, "firecracker": .12, "fountain": .8}[kind]
        samples = array.array("h")
        phase = 0.0
        for i in range(int(rate * duration)):
            t = i / rate
            noise = random.uniform(-1, 1)
            if kind == "launch":
                phase += math.tau * (260 - 170*t/duration) / rate
                value, env = math.sin(phase)*.35 + noise*.32, (t/duration)**.7
            elif kind == "burst":
                phase += math.tau * (95 + 35*math.sin(t*18)) / rate
                value, env = math.sin(phase)*.48 + noise*.8, math.exp(-t*7)
            elif kind in ("crackle", "firecracker"):
                value = noise * (1.0 if random.random() < .18 else .12)
                env = math.exp(-t*(12 if kind == "crackle" else 24))
            else:
                phase += math.tau * random.uniform(700,1800) / rate
                value, env = math.sin(phase)*.22 + noise*.48, .7 + .3*math.sin(t*25)
            samples.append(int(max(-1,min(1,value*env))*25000))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name, volume=1.0):
        if self.enabled:
            try:
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.set_volume(volume)
                    channel.play(self.sounds[name])
            except (pygame.error, KeyError):
                pass


class FireworksSimulation:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MU Fireworks Simulator v0.3 — Total Show Overhaul")
        self.audio = SoundEngine()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.glow = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.small = pygame.font.SysFont("consolas", 14)
        self.big = pygame.font.SysFont("consolas", 30, bold=True)

        self.particles = []
        self.rockets = []
        self.backyard = True
        self.auto_show = False
        self.auto_clock = 0.0
        self.auto_interval = 1.0
        self.paused = False
        self.show_hud = True
        self.speed = 1.0
        self.selected_effect = -1
        self.wind = random.uniform(-9, 9)
        self.wind_clock = 0.0
        self.firecracker_clock = 0.0
        self.firecracker_active = False
        self.candle_clock = 0.0
        self.candle_shots = 0
        self.fountain_active = False
        self.fountain_clock = 0.0
        self.running = True
        self.fullscreen = False
        self.elapsed = 0.0
        self.launch_count = 0
        self.stars = [
            (random.randrange(WIDTH), random.randrange(25, 500),
             random.choice([1, 1, 1, 1, 2]), random.uniform(0.5, 1.0))
            for _ in range(230)
        ]
        self.gradient_sky = self.make_gradient()
        self.houses = self.make_houses()
        self.ground = self.make_ground()

    def make_gradient(self):
        surface = pygame.Surface((WIDTH, HEIGHT))
        top = (3, 5, 16) if not self.backyard else (7, 12, 29)
        bottom = (8, 11, 24) if not self.backyard else (22, 31, 48)
        for y in range(HEIGHT):
            color = mix_color(top, bottom, y / HEIGHT)
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        return surface

    def rebuild_background(self):
        self.gradient_sky = self.make_gradient()

    def make_houses(self):
        return [
            pygame.Rect(-15, 595, 255, 125),
            pygame.Rect(285, 560, 235, 160),
            pygame.Rect(785, 580, 230, 140),
            pygame.Rect(1040, 548, 280, 172),
        ]

    def make_ground(self):
        rng = random.Random(2205)
        return [(x, rng.randint(24, 78), rng.randint(12, 30))
                for x in range(-30, WIDTH + 40, 35)]

    def launch(self, target=None, effect=None):
        if target is None:
            target = (random.randint(150, WIDTH - 150),
                      random.randint(135, 360))
        tx, ty = target
        sx = random.randint(90, WIDTH - 90)
        sy = HEIGHT - random.randint(22, 48)
        dx, dy = tx - sx, ty - sy
        distance = max(1.0, math.hypot(dx, dy))
        speed = random.uniform(440, 565)
        vx = dx / distance * speed + random.uniform(-24, 24)
        vy = dy / distance * speed
        fuse = clamp(distance / speed, 0.48, 1.38) * random.uniform(0.88, 1.12)

        palette = random.choice(PALETTES)
        hue = random.choice(palette)
        chosen = self.selected_effect if effect is None else effect
        if chosen < 0:
            chosen = random.randrange(len(EFFECTS))
        self.rockets.append(Rocket(sx, sy, vx, vy, hue, chosen, fuse=fuse))
        self.audio.play("launch", 0.35)
        self.launch_count += 1

    def add_particle(self, x, y, vx, vy, radius, color, life,
                     drag=0.985, gravity=GRAVITY, glow=True,
                     flicker=0.0, split=False):
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(Particle(
                x, y, vx, vy, radius, color, life, life,
                drag=drag, gravity=gravity, glow=glow,
                flicker=flicker, split=split
            ))

    def burst(self, x, y, base_color, effect):
        palette = random.choice(PALETTES) if random.random() < 0.32 else [
            base_color, mix_color(base_color, (255, 255, 255), 0.28),
            mix_color(base_color, (255, 185, 85), 0.22)
        ]
        count = random.randint(135, 245)
        base_speed = random.uniform(145, 260)
        rotation = random.uniform(0, TAU)
        ring_count = random.randint(2, 4) if effect == 3 else 1

        for i in range(count):
            if effect == 3:  # Ring
                angle = rotation + TAU * (i / count) + random.uniform(-0.025, 0.025)
                speed = random.uniform(165, 215)
                life = random.uniform(0.78, 1.18)
                drag = random.uniform(0.982, 0.99)
                color = random.choice(palette)
            elif effect == 4:  # Palm
                angle = rotation + random.uniform(-0.11, 0.11)
                if i % 2:
                    angle += math.pi
                speed = random.uniform(150, 255)
                life = random.uniform(1.25, 2.0)
                drag = random.uniform(0.966, 0.982)
                color = random.choice(palette)
            elif effect == 2:  # Willow
                angle = random.uniform(0, TAU)
                speed = random.uniform(90, 195)
                life = random.uniform(1.55, 2.65)
                drag = random.uniform(0.968, 0.982)
                color = mix_color(random.choice(palette), (255, 183, 85),
                                  random.uniform(0.05, 0.38))
            elif effect == 5:  # Crackle
                angle = random.uniform(0, TAU)
                speed = random.uniform(75, base_speed * 1.05)
                life = random.uniform(0.48, 1.0)
                drag = random.uniform(0.975, 0.988)
                color = random.choice(palette)
            elif effect == 6:  # Strobe
                angle = random.uniform(0, TAU)
                speed = random.uniform(base_speed * 0.5, base_speed)
                life = random.uniform(0.9, 1.45)
                drag = random.uniform(0.98, 0.99)
                color = random.choice(palette)
            elif effect == 7:  # Brocade
                angle = random.uniform(0, TAU)
                speed = random.uniform(105, 210)
                life = random.uniform(1.45, 2.4)
                drag = random.uniform(0.972, 0.985)
                color = (255, random.randint(185, 225), random.randint(90, 150))
            else:  # Peony / Chrysanthemum
                angle = rotation + random.uniform(0, TAU)
                speed = random.uniform(base_speed * 0.55, base_speed * 1.12)
                life = random.uniform(0.75, 1.4) if effect == 1 else random.uniform(0.65, 1.1)
                drag = random.uniform(0.98, 0.991)
                color = random.choice(palette)

            if effect != 3:
                angle += random.uniform(-0.035, 0.035)
            speed *= random.uniform(0.9, 1.1)
            vx = math.cos(angle) * speed + random.uniform(-8, 8)
            vy = math.sin(angle) * speed + random.uniform(-8, 8)
            split = effect == 5 and random.random() < 0.22
            flicker = 0.28 if effect == 6 else (0.22 if effect == 5 else 0.06)
            self.add_particle(
                x + random.uniform(-2, 2), y + random.uniform(-2, 2),
                vx, vy, random.uniform(1.1, 2.7), color, life,
                drag=drag, flicker=flicker, split=split
            )

        # Bright core flash and a few secondary glitter sparks.
        for _ in range(random.randint(18, 32)):
            angle = random.uniform(0, TAU)
            speed = random.uniform(25, 125)
            life = random.uniform(0.14, 0.38)
            self.add_particle(x, y, math.cos(angle) * speed,
                              math.sin(angle) * speed, random.uniform(1.5, 3.2),
                              (255, 250, 225), life, drag=0.96, flicker=0.08)

        # A soft smoke cloud after the shell breaks.
        for _ in range(random.randint(7, 13)):
            angle = random.uniform(0, TAU)
            distance = random.uniform(5, 30)
            self.add_particle(
                x + math.cos(angle) * distance, y + math.sin(angle) * distance,
                random.uniform(-9, 9), random.uniform(-18, 5),
                random.uniform(5, 10), (105, 110, 125),
                random.uniform(1.1, 2.0), drag=0.96, gravity=-4,
                glow=False
            )

        # Brocade and willow get a delayed-looking glitter rain.
        if effect in (2, 7):
            for _ in range(38):
                angle = random.uniform(0, TAU)
                speed = random.uniform(35, 115)
                self.add_particle(
                    x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                    random.uniform(1.0, 1.8), (255, 205, 115),
                    random.uniform(1.3, 2.2), drag=0.97, flicker=0.16
                )

    def update(self, dt):
        if self.paused:
            return
        dt *= self.speed
        self.elapsed += dt
        self.wind_clock += dt
        if self.wind_clock >= 5.0:
            self.wind_clock = 0
            self.wind = random.uniform(-15, 15)
        if self.firecracker_active:
            self.firecracker_clock += dt
            if self.firecracker_clock >= .105:
                self.firecracker_clock = 0
                for _ in range(random.randint(2, 4)):
                    x, y = random.randint(120, WIDTH-120), HEIGHT-random.randint(28,85)
                    for _ in range(random.randint(5,10)):
                        self.add_particle(x,y,random.uniform(-75,75),random.uniform(-155,-35),random.uniform(1,2),random.choice([(255,190,90),(255,235,180)]),random.uniform(.18,.38),drag=.94,flicker=.25)
                self.audio.play("firecracker", .35)
        if self.candle_shots > 0:
            self.candle_clock += dt
            if self.candle_clock >= .38:
                self.candle_clock = 0
                self.candle_shots -= 1
                self.launch((random.randint(260,WIDTH-260),random.randint(160,390)))
        if self.fountain_active:
            self.fountain_clock += dt
            if self.fountain_clock >= .018:
                self.fountain_clock = 0
                for _ in range(5):
                    self.add_particle(WIDTH*.5+random.uniform(-22,22),HEIGHT-55,random.uniform(-85,85),random.uniform(-310,-130),random.uniform(1,2.4),random.choice([(255,180,65),(255,230,150),(255,250,220)]),random.uniform(.45,1.15),drag=.975,flicker=.2)
                if random.random() < .08:
                    self.audio.play("fountain", .12)

        if self.auto_show:
            self.auto_clock += dt
            if self.auto_clock >= self.auto_interval:
                self.auto_clock = 0
                self.auto_interval = random.uniform(0.48, 1.35)
                self.launch()

        for rocket in self.rockets[:]:
            if rocket.update(dt, self.particles):
                self.burst(rocket.x, rocket.y, rocket.hue, rocket.effect)
                self.audio.play("burst", .65)
                if rocket.effect == 5:
                    self.audio.play("crackle", .5)
                self.rockets.remove(rocket)

        children = []
        alive = []
        for particle in self.particles:
            particle.vx += self.wind * dt * (0.12 if particle.smoke else 0.035)
            if particle.update(dt, children):
                alive.append(particle)
        self.particles = alive
        if children:
            self.particles.extend(children[:max(0, MAX_PARTICLES - len(self.particles))])

    def draw_background(self):
        self.canvas.blit(self.gradient_sky, (0, 0))
        for sx, sy, radius, phase in self.stars:
            twinkle = 0.72 + 0.28 * math.sin(self.elapsed * 1.8 + phase * 8)
            brightness = int(135 + 105 * twinkle)
            pygame.draw.circle(self.canvas, (brightness, brightness, brightness),
                               (sx, sy), radius)

        if self.backyard:
            # Distant tree line and ground.
            for x, height, radius in self.ground:
                pygame.draw.circle(self.canvas, (8, 17, 19),
                                   (x, 650), radius)
                pygame.draw.rect(self.canvas, (8, 17, 19),
                                 (x - 3, 625, 6, 45))
            pygame.draw.rect(self.canvas, (9, 16, 18), (0, 650, WIDTH, 70))

            for index, rect in enumerate(self.houses):
                pygame.draw.rect(self.canvas, (11, 15, 23), rect)
                roof = [(rect.left - 18, rect.top + 8),
                        (rect.centerx, rect.top - 58),
                        (rect.right + 18, rect.top + 8)]
                pygame.draw.polygon(self.canvas, (8, 11, 18), roof)
                for wx in range(rect.left + 24, rect.right - 15, 52):
                    for wy in range(rect.top + 25, rect.bottom - 15, 43):
                        seed = wx * 13 + wy + index * 71
                        if random.Random(seed).random() < 0.28:
                            pygame.draw.rect(self.canvas, (105, 88, 52),
                                             (wx, wy, 17, 22))
            # Subtle horizon glow.
            pygame.draw.ellipse(self.canvas, (13, 23, 29),
                                (-120, 610, WIDTH + 240, 95))

    def draw_rocket(self, rocket):
        x, y = int(rocket.x), int(rocket.y)
        pygame.draw.circle(self.glow, (55, 35, 12), (x, y), 13)
        pygame.draw.circle(self.canvas, (255, 250, 220), (x, y), 3)
        pygame.draw.circle(self.canvas, (255, 160, 65), (x, y), 6, 1)

    def draw_text(self, text, x, y, color=(225, 232, 245), font=None):
        image = (font or self.small).render(text, True, color)
        self.canvas.blit(image, (x, y))

    def draw_hud(self):
        if not self.show_hud:
            return
        panel = pygame.Surface((WIDTH, 92), pygame.SRCALPHA)
        panel.fill((4, 7, 16, 175))
        self.canvas.blit(panel, (0, 0))
        self.draw_text("MU FIREWORKS SIMULATOR", 18, 12, (255, 226, 170), self.font)
        self.draw_text("TOTAL SHOW OVERHAUL  /  v0.3.0", 18, 39, (150, 190, 255), self.small)

        effect_name = "RANDOM" if self.selected_effect < 0 else EFFECTS[self.selected_effect].upper()
        status = "PAUSED" if self.paused else ("AUTO SHOW" if self.auto_show else "MANUAL")
        self.draw_text(
            f"{status}   |   STYLE: {effect_name}   |   SPEED: {self.speed:.2f}x",
            340, 14, (225, 235, 250), self.small
        )
        self.draw_text(
            f"SCENE: {'BACKYARD' if self.backyard else 'DEEP SPACE'}"
            f"   |   WIND: {self.wind:+.0f}   |   SHELLS: {self.launch_count}   |   SPARKS: {len(self.particles):,}",
            340, 38, (165, 190, 215), self.small
        )
        self.draw_text(
            "CLICK launch  SPACE shell  1-8 styles  Q firecrackers  W roman candles  E fountain",
            18, 66, (205, 215, 230), self.small
        )
        self.draw_text(
            "T bottle rocket  B scene  R auto  P pause  +/- speed  H HUD  F fullscreen  C clear",
            18, 84, (165, 185, 210), self.small
        )

    def render(self):
        self.draw_background()
        self.glow.fill((0, 0, 0))
        for particle in self.particles:
            particle.draw(self.canvas, self.glow)
        for rocket in self.rockets:
            self.draw_rocket(rocket)

        # Additive glow layer, kept separate from the crisp spark cores.
        self.canvas.blit(self.glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.draw_hud()

        window = self.screen.get_size()
        if window != (WIDTH, HEIGHT):
            scaled = pygame.transform.smoothscale(self.canvas, window)
            self.screen.blit(scaled, (0, 0))
        else:
            self.screen.blit(self.canvas, (0, 0))
        pygame.display.flip()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    def clear(self):
        self.particles.clear()
        self.rockets.clear()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_SPACE:
                self.launch()
            elif event.key == pygame.K_q:
                self.firecracker_active = not self.firecracker_active
            elif event.key == pygame.K_w:
                self.candle_shots = 8
                self.candle_clock = 0
            elif event.key == pygame.K_e:
                self.fountain_active = not self.fountain_active
            elif event.key == pygame.K_t:
                self.launch((random.randint(350,WIDTH-350),random.randint(130,300)),effect=5)
            elif event.key == pygame.K_b:
                self.backyard = not self.backyard
                self.rebuild_background()
            elif event.key == pygame.K_r:
                self.auto_show = not self.auto_show
                self.auto_clock = 0
            elif event.key == pygame.K_p:
                self.paused = not self.paused
            elif event.key == pygame.K_h:
                self.show_hud = not self.show_hud
            elif event.key == pygame.K_f:
                self.toggle_fullscreen()
            elif event.key == pygame.K_c:
                self.clear()
                self.firecracker_active = False
                self.fountain_active = False
                self.candle_shots = 0
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.speed = min(2.5, round(self.speed + 0.1, 2))
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.speed = max(0.25, round(self.speed - 0.1, 2))
            elif pygame.K_1 <= event.key <= pygame.K_8:
                self.selected_effect = event.key - pygame.K_1
            elif event.key == pygame.K_0:
                self.selected_effect = -1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert window coordinates back to the fixed simulation canvas.
            ww, wh = self.screen.get_size()
            target = (event.pos[0] * WIDTH / max(1, ww),
                      event.pos[1] * HEIGHT / max(1, wh))
            self.launch(target)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.04)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    FireworksSimulation().run()
