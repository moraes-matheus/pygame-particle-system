import math
import random

import pygame
import vnoise

import effects

#debug - This is for testing moving the particle using perlin noise
# But because my current pc can't handle dooing the algorithm on the fly
# I need to cache the values.
noise = vnoise.Noise()
NOISE_SIZE = 1024

noise_values = [noise.noise1(i / 100) for i in range(NOISE_SIZE)]


# (255, 0 , 0, 0, 0, 255, 0, 0)
# Color index = i * 4 | 0 * 4 = 0 Color 1, 1 * 4 = 4 Color 2...

#Thresholds = (0, 0.2) -> first color start at 0, if color reaches 20% of total lifetime, color 2 gets applied
# colors and thresholds size needs to be the same
class ColorData:
    def __init__(self, colors, thresholds):
        self.color = colors
        self.threshoulds = thresholds

class Particle:
    def __init__(self):
        self.x = None
        self.y = None
        self.x_direction = None
        self.y_direction = None
        self.initial_radius = None
        self.radius = None
        self.current_life_time = None
        self.total_life_time = None
        self.velocity = None
        self.alpha = None
        self.color = None

        self.next = None

        self.cos = True
        self.noise_offset = None
    def init(self, x, y, x_direction, y_direction, radius, life_time, velocity, color):
        self.x = x
        self.y = y
        self.x_direction = x_direction
        self.y_direction = y_direction
        self.initial_radius = radius
        self.radius = radius
        self.current_life_time = 0.0
        self.total_life_time = life_time
        self.velocity = velocity
        self.alpha = 255
        self.color = color
        self.noise_offset = random.random() * 1000

    def update(self, delta_time):
        self.current_life_time += delta_time

        if self.current_life_time >= self.total_life_time:
            return False
            #Debug immortal particles
            #self.current_life_time = self.total_life_time * 0.01

		# Here its a little mess because Im testing different movement types
        if self.cos:
            # The greater the first value, the thiner it gets
            # The greater the seconds value, the wide it spreads
            # If I update the y by the x value it does a kinda of 3d effect (cylinder)
            # Otherwise it just follows the wave
            # x cos y sin gets round motion
            #self.x -= math.cos(5 * self.current_life_time) * 1

            index = int((self.current_life_time * 5 + self.noise_offset) * 100) % NOISE_SIZE
            self.x += noise_values[index] * 1
            #self.x += noise.noise1(5 * self.current_life_time) * 3
            self.y += self.y_direction * self.velocity * delta_time
        else:
            self.x += self.x_direction * self.velocity * delta_time
            self.y += self.y_direction * self.velocity * delta_time
                

        life = 1 - self.current_life_time / self.total_life_time

        # update size based on life
        self.radius = int(self.initial_radius * life)
        
        # update alpha based on life
        # In order for our cache to not be so big, particles can have 14 diferent alpha values
        self.alpha = 17 + int(life * 14) * 17
        
        if life < 0.6:
            self.color = (255,255,0)

        return True
        
    def set_next(self, particle):
        self.next = particle
    
    def get_next(self):
            return self.next

class ParticlePool:
    def __init__(self):
        self.pool_size = 999
        self.particles = [Particle() for _ in range(self.pool_size)]

        for i in range(len(self.particles) - 1):
            self.particles[i].set_next(self.particles[i + 1]) 
        
        self.particles[self.pool_size - 1].set_next(None)
        
        self.first_available = self.particles[0]

    def create(self, x, y, x_direction, y_direction, radius, life_time, velocity, colors = None):
        if self.first_available is None:
            return None
        
        particle = self.first_available
        self.first_available = particle.get_next()
        particle.next = None

        particle.init(x, y, x_direction, y_direction, radius, life_time, velocity, colors)

        return particle
    
    def release(self, particle):
        particle.next = self.first_available
        self.first_available = particle

class ParticleSystem:
    def __init__(self, particle_pool, gravity = False):
        self.particle_pool = particle_pool
        self.gravity = gravity

        self.total_time = 0
        self.active_particles = []

        self.cached_surfaces = {}
        self.surfaces_to_blit = []

        self.square = False

    def add(self, x, y, x_direction, y_direction, radius, life_time, velocity, color=(0,0,0)):
        particle = self.particle_pool.create(x, y, x_direction, y_direction, radius, life_time, velocity, color)
        if particle is not None:
            self.active_particles.append(particle)
            
    def _kill_particle(self, particle, index):
        # We use swap-and-pop here to delete the item from an unsorted array in O(1).
        self.active_particles[index] = self.active_particles[-1]
        self.active_particles.pop()

        self.particle_pool.release(particle)
    
    def update(self, delta_time):
        # We traverse in reverse order to apply swap-and-pop O(1) removal to dead particles.
        self.surfaces_to_blit.clear()
        for i in range(len(self.active_particles) - 1, -1, -1):
            particle = self.active_particles[i]

            if not self.active_particles[i].update(delta_time):
                self._kill_particle(particle, i)
                continue
            
            if self.gravity:
                particle.y_direction += 1.5 * delta_time

            key = (particle.radius, particle.color, particle.alpha)
            surface = self.cached_surfaces.get(key)

            if surface is None:
                radius = particle.radius
                color = pygame.Color(particle.color[0], particle.color[1], particle.color[2], particle.alpha)

                surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA).convert_alpha()

                if self.square:
                    surface.fill(color)
                else:
                    pygame.draw.circle(surface, color, (radius, radius), radius)

                self.cached_surfaces[key] = surface

            self.surfaces_to_blit.append((surface, (particle.x, particle.y)))

    def draw(self, surface):
        surface.fblits(self.surfaces_to_blit)

    def __len__(self):
        return len(self.active_particles)

colors = [(255, 230, 0), (255, 100, 0), (150, 0, 0)]

pygame.init()
screen = pygame.display.set_mode((640, 320))
running = True

particle_pool = ParticlePool()
particle_system = ParticleSystem(particle_pool, gravity=False)

clock = pygame.Clock()
while running:
    delta_time = clock.tick(60) / 1000
    pygame.display.set_caption(str(f"FPS: {clock.get_fps():.0f} | Particles alive: {len(particle_system)}"))

    mouse_down = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            for i in range(10):
                mouse_pos = pygame.mouse.get_pos()
                color = random.randint(0, 2)
                pc = (colors[color][0], colors[color][1], colors[color][2])
                particle_system.add(mouse_pos[0], mouse_pos[1], random.random() * 2 - 1, -1, (random.randint(2,8)), (random.random() * 2), 50, pc)
        if event.type == pygame.MOUSEBUTTONDOWN:
            effects.explosion(pygame.mouse.get_pos(), particle_system)
    
    screen.fill(pygame.Color("grey0"))


    #particle_system.add(random.randint(295, 305), random.randint(245, 255), random.random() * 2 - 1, -1, random.randint(2,8), random.random() * 2, 50, (255,0,0))
    particle_system.add(random.randint(290, 300), random.randint(240, 250), random.random() * 2 - 1, -1, random.randint(2,8), random.random() * 2, 50, (255,0,0))

    particle_system.update(delta_time)
    particle_system.draw(screen)

    pygame.display.flip()
pygame.quit()
exit()
