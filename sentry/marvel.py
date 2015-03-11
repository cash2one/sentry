"""
Some names from marvel characters.
These name was picked up for default environment name.
"""
import random


_names = [
    'Avengers',
    'Iron-Man',
    'Captain',
    'Hulk',
    'Spider-Man',
    'Thor',
    'X-Men',
    'Storm',
    'Fantastic',
    'Black-Widow',
    'S.H.I.E.L.D.',
    'Guardians',
]


def pick_up():
    return random.choice(_names)
