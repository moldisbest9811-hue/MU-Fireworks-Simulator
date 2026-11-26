"""
MU Fireworks Simulator — 2D Prototype
Visual-only particle simulation. No real-world firework construction or launch instructions.

Requirements:
    py -m pip install pygame-ce

Run:
    py mu_fireworks.py

Controls:
    Left click  Launch a virtual bottle-rocket effect
    SPACE       Launch a random virtual firework
    B           Toggle black sky / backyard
    R           Toggle automatic random launches
    C           Clear particles
    ESC         Quit
"""

import math
import random
import sys
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 1280, 720
FPS = 60
GRAVITY = 115.0
MAX_PARTICLES = 9000

BLACK = (5, 7, 15)
SKY_TOP = (5, 8, 20)
SKY_BOTTOM = (17, 23, 39)


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
    glow: bool = True
    flicker: float = 0.0

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False

        drag_factor = self.drag ** (dt * 60.0)
        self.vx *= drag_factor
        self.vy *= drag_factor
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True

    def draw(self, surface):
        remaining = clamp(self.life / self.max_life, 0.0, 1.0)
        alpha = int(255 * (remaining ** 0.72))
        if self.flicker and random.random() < self.flicker:
            alpha = int(alpha * random.uniform(0.25, 0.75))

        color = tuple(int(channel * alpha / 255) for channel in self.color)
        x, y = int(self.x), int(self.y)
        radius = max(1, int(self.radius * (0.55 + remaining * 0.45)))

        if self.glow and radius >= 2:
            glow_radius = radius * 3
            glow_color = tuple(int(channel * 0.20 * alpha / 255) for channel in self.color)
            pygame.draw.circle(surface, glow_color, (x, y), glow_radius)

        pygame.draw.circle(surface, color, (x, y), radius)


@dataclass
class Rocket:
    x: float
    y: float
    vx: float
    vy: float
    age: float = 0.0
    fuse: float = 0.85
    hue: tuple = (255, 210, 120)
    trail_clock: float = 0.0

    def update(self, dt, particles):
        self.age += dt
        self.trail_clock += dt

        self.vx += random.uniform(-7.0, 7.0) * dt
        self.vy += 26.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        while self.trail_clock >= 0.018:
            self.trail_clock -= 0.018
            if len(particles) < MAX_PARTICLES:
                particles.append(Particle(
                    self.x + random.uniform(-1.5, 1.5),
                    self.y + random.uniform(-1.5, 1.5),
                    -self.vx * 0.10 + random.uniform(-18, 18),
                    -self.vy * 0.10 + random.uniform(-18, 18),
                    random.uniform(1.0, 2.2),
                    random.choice([self.hue, (255, 245, 205), (255, 150, 65)]),
                    random.uniform(0.18, 0.42),
                    0.42,
                    drag=0.94,
                    flicker=0.15,
                ))

        return self.age >= self.fuse or self.y < 65


class FireworksSimulation:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MU Fireworks Simulator — 2D Prototype")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.small_font = pygame.font.SysFont("consolas", 14)

        self.particles = []
        self.rockets = []
        self.backyard = False
        self.auto_launch = False
        self.auto_clock = 0.0
        self.running = True
        self.stars = [
            (random.randrange(WIDTH), random.randrange(25, 430), random.choice([1, 1, 1, 2]))
            for _ in range(150)
        ]
        self.houses = self.make_backyard_silhouette()

    def make_backyard_silhouette(self):
        return [
            pygame.Rect(0, 590, 260, 130),
            pygame.Rect(300, 555, 230, 165),
            pygame.Rect(790, 575, 220, 145),
            pygame.Rect(1040, 545, 300, 175),
        ]

    def launch(self, target=None):
        if target is None:
            target_x = random.randint(180, WIDTH - 180)
            target_y = random.randint(145, 355)
        else:
            target_x, target_y = target

        start_x = random.randint(90, WIDTH - 90)
        start_y = HEIGHT - random.randint(22, 55)
        dx = target_x - start_x
        dy = target_y - start_y
        distance = max(1.0, math.hypot(dx, dy))
        speed = random.uniform(440.0, 560.0)

        vx = dx / distance * speed + random.uniform(-28, 28)
        vy = dy / distance * speed
        fuse = clamp(distance / speed, 0.48, 1.35) * random.uniform(0.88, 1.12)

        hue = random.choice([
            (255, 190, 75), (255, 85, 75), (100, 175, 255),
            (150, 255, 145), (220, 135, 255), (255, 245, 210)
        ])
        self.rockets.append(Rocket(start_x, start_y, vx, vy, fuse=fuse, hue=hue))

    def burst(self, x, y, base_color):
        if len(self.particles) >= MAX_PARTICLES:
            return

        style = random.choice(["sphere", "willow", "chrysanthemum", "peony"])
        count = random.randint(95, 175)
        base_speed = random.uniform(105, 255)

        for _ in range(count):
            angle = random.uniform(0, math.tau)
            if style == "willow":
                speed = random.uniform(65, 175)
                life = random.uniform(1.3, 2.35)
                drag = random.uniform(0.965, 0.982)
                color = mix_color(base_color, (255, 175, 70), random.uniform(0.0, 0.45))
            elif style == "chrysanthemum":
                speed = random.uniform(base_speed * 0.55, base_speed * 1.15)
                life = random.uniform(0.75, 1.45)
                drag = random.uniform(0.982, 0.991)
                color = mix_color(base_color, (255, 255, 235), random.uniform(0.0, 0.28))
            elif style == "peony":
                speed = random.uniform(base_speed * 0.45, base_speed)
                life = random.uniform(0.55, 1.05)
                drag = random.uniform(0.978, 0.989)
                color = base_color
            else:
                speed = random.uniform(base_speed * 0.5, base_speed * 1.05)
                life = random.uniform(0.7, 1.35)
                drag = random.uniform(0.98, 0.99)
                color = mix_color(base_color, (255, 255, 255), random.uniform(0.0, 0.35))

            angle += random.uniform(-0.035, 0.035)
            speed *= random.uniform(0.88, 1.12)
            vx = math.cos(angle) * speed + random.uniform(-10, 10)
            vy = math.sin(angle) * speed + random.uniform(-10, 10)

            self.particles.append(Particle(
                x + random.uniform(-2, 2),
                y + random.uniform(-2, 2),
                vx, vy,
                random.uniform(1.1, 2.5),
                color,
                life, life,
                drag=drag,
                flicker=random.uniform(0.0, 0.12),
            ))

        for _ in range(18):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(25, 100)
            life = random.uniform(0.12, 0.28)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(1.5, 3.0), (255, 250, 220), life, life,
                drag=0.96, glow=True
            ))

    def draw_background(self):
        self.screen.fill(BLACK)
        if self.backyard:
            for y in range(HEIGHT):
                amount = y / HEIGHT
                color = mix_color(SKY_TOP, SKY_BOTTOM, amount)
                pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        else:
            for y in range(HEIGHT):
                amount = y / HEIGHT
                color = mix_color((1, 2, 8), (7, 10, 22), amount)
                pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

        for sx, sy, radius in self.stars:
            brightness = random.randint(125, 220)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (sx, sy), radius)

        if self.backyard:
            pygame.draw.rect(self.screen, (10, 17, 19), (0, 650, WIDTH, 70))
            for x in range(-20, WIDTH + 40, 65):
                height = random.Random(x).randint(35, 85)
                pygame.draw.circle(self.screen, (8, 18, 17), (x, 650), height // 2)
                pygame.draw.rect(self.screen, (8, 18, 17), (x - 5, 620, 10, 50))

            for rect in self.houses:
                pygame.draw.rect(self.screen, (12, 16, 23), rect)
                roof = [
                    (rect.left - 15, rect.top + 8),
                    (rect.centerx, rect.top - 55),
                    (rect.right + 15, rect.top + 8),
                ]
                pygame.draw.polygon(self.screen, (9, 12, 19), roof)
                for wx in range(rect.left + 25, rect.right - 15, 55):
                    for wy in range(rect.top + 28, rect.bottom - 15, 45):
                        if random.Random(wx * 13 + wy).random() < 0.23:
                            pygame.draw.rect(self.screen, (95, 82, 48), (wx, wy, 17, 22))

    def draw_rocket(self, rocket):
        pygame.draw.circle(self.screen, (255, 245, 205), (int(rocket.x), int(rocket.y)), 3)
        pygame.draw.circle(self.screen, (255, 150, 65), (int(rocket.x), int(rocket.y)), 6, 1)

    def update(self, dt):
        self.auto_clock += dt
        if self.auto_launch and self.auto_clock >= random.uniform(0.65, 1.25):
            self.auto_clock = 0.0
            self.launch()

        for rocket in self.rockets[:]:
            if rocket.update(dt, self.particles):
                self.burst(rocket.x, rocket.y, rocket.hue)
                self.rockets.remove(rocket)

        self.particles = [p for p in self.particles if p.update(dt)]

    def draw_ui(self):
        mode = "BACKYARD" if self.backyard else "BLACK SKY"
        auto = "ON" if self.auto_launch else "OFF"
        lines = [
            "MU FIREWORKS SIMULATOR  |  2D PARTICLE PROTOTYPE",
            f"SCENE: {mode}    AUTO: {auto}    PARTICLES: {len(self.particles)}",
            "CLICK: launch bottle rocket   SPACE: random launch   B: scene   R: auto   C: clear   ESC: quit",
        ]
        for index, line in enumerate(lines):
            image = self.small_font.render(line, True, (205, 215, 230))
            self.screen.blit(image, (18, 15 + index * 22))

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.035)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.launch()
                    elif event.key == pygame.K_b:
                        self.backyard = not self.backyard
                    elif event.key == pygame.K_r:
                        self.auto_launch = not self.auto_launch
                    elif event.key == pygame.K_c:
                        self.particles.clear()
                        self.rockets.clear()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.launch(event.pos)

            self.update(dt)
            self.draw_background()

            for particle in self.particles:
                particle.draw(self.screen)
            for rocket in self.rockets:
                self.draw_rocket(rocket)

            self.draw_ui()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    FireworksSimulation().run()
