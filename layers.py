import random
from math import hypot

import noise
from noise.perlin import SimplexNoise
from PIL import Image

from alpha_shape import alpha_shape


class Layer:
    def translate(self, x, y):
        return Translate(self, x, y)
    def scale(self, x, y):
        return Scale(self, x, y)
    def power(self, power):
        return Power(self, power)
    def add(self, other):
        return Add(self, other)
    def subtract(self, other):
        return Subtract(self, other)
    def multiply(self, other):
        return Multiply(self, other)
    def threshold(self, threshold):
        return Threshold(self, threshold)
    def clamp(self, lo=0, hi=1):
        return Clamp(self, lo, hi)
    def normalize(self, lo, hi, new_lo, new_hi):
        return Normalize(self, lo, hi, new_lo, new_hi)
    def filter_points(self, points, lo, hi):
        return [(x, y) for x, y in points if lo <= self.get(x, y) < hi]
    def alpha_shape(self, points, lo, hi, random_alpha, method):
        points = self.filter_points(points, lo, hi)
        return alpha_shape(points, random_alpha, method)
    def save(self, path, x1, y1, x2, y2, lo=0, hi=1):
        data = []
        for y in range(y1, y2):
            for x in range(x1, x2):
                v = (self.get(x, y) - lo) / (hi - lo)
                v = int(v * 255)
                v = min(v, 255)
                v = max(v, 0)
                data.append(chr(v))
        im = Image.frombytes('L', (x2 - x1, y2 - y1), ''.join(data).encode())
        im.save(path, 'png')

class Constant(Layer):
    def __init__(self, value):
        self.value = value
    def get(self, x, y):
        return self.value

class Noise(Layer):
    def __init__(self, octaves=1, algo="simplex"):
        self.octaves = octaves
        self.algo = algo
    def get(self, x, y):
        if self.algo == "simplex":
            out = noise.snoise2(x, y, self.octaves)
        if self.algo == "snoise":
            out = SimplexNoise(period=self.octaves, randint_function=random.randint).noise2(x, y)
        if self.algo == "pnoise":
            out = noise.pnoise2(x, y, self.octaves, self.octaves)
        return out

class Translate(Layer):
    def __init__(self, layer, x, y):
        self.layer = layer
        self.x = x
        self.y = y
    def get(self, x, y):
        return self.layer.get(self.x + x, self.y + y)

class Scale(Layer):
    def __init__(self, layer, x, y):
        self.layer = layer
        self.x = x
        self.y = y
    def get(self, x, y):
        return self.layer.get(self.x * x, self.y * y)

class Power(Layer):
    def __init__(self, layer, power):
        self.layer = layer
        self.power = power
    def get(self, x, y):
        return self.layer.get(x, y) ** self.power

class Add(Layer):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def get(self, x, y):
        return self.a.get(x, y) + self.b.get(x, y)

class Subtract(Layer):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def get(self, x, y):
        return self.a.get(x, y) - self.b.get(x, y)

class Multiply(Layer):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def get(self, x, y):
        return self.a.get(x, y) * self.b.get(x, y)

class Threshold(Layer):
    def __init__(self, layer, threshold):
        self.layer = layer
        self.threshold = threshold
    def get(self, x, y):
        return 0 if self.layer.get(x, y) < self.threshold else 1

class Clamp(Layer):
    def __init__(self, layer, lo=0, hi=1):
        self.layer = layer
        self.lo = lo
        self.hi = hi
    def get(self, x, y):
        v = self.layer.get(x, y)
        v = min(v, self.hi)
        return max(v, self.lo)

class Normalize(Layer):
    def __init__(self, layer, lo, hi, new_lo, new_hi):
        self.layer = layer
        self.lo = lo
        self.hi = hi
        self.new_lo = new_lo
        self.new_hi = new_hi
    def get(self, x, y):
        v = self.layer.get(x, y)
        p = (v - self.lo) / (self.hi - self.lo)
        return self.new_lo + p * (self.new_hi - self.new_lo)

class Distance(Layer):
    def __init__(self, x, y, maximum):
        self.x = x
        self.y = y
        self.maximum = maximum
    def get(self, x, y):
        return hypot(x - self.x, y - self.y) / self.maximum
