import pygame
import math

def explosion(pos, particle_system):    
        x, y = pos

        particle_count = 20

        for i in range(particle_count):

            angle = (2 * math.pi / particle_count) * i

            x_direction = math.cos(angle)
            y_direction = math.sin(angle)

            particle_system.add(
                x, y,
                x_direction,

                y_direction,
                radius=6,
                life_time=2,
                velocity=100
            )