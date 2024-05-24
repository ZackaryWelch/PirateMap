import math
import random

import cairocffi as cairo
from colour import Color
from shapely.geometry import MultiPolygon, Point, Polygon

import graph
import layers
from poisson_disc import poisson_disc
from xkcd import xkcdify

WATER_GRADIENT = 5

def make_layer(algo):
    x = layers.Noise(8, algo).add(layers.Constant(0.6)).clamp()
    x = x.translate(random.random() * 1000, random.random() * 1000)
    x = x.scale(0.005, 0.005)
    x = x.subtract(layers.Distance(256, 256, 256))
    return x

def color_scale(begin, end):
    step = tuple([float(end[i] - begin[i]) / WATER_GRADIENT for i in range(3)])

    def mul(step, value):
        return tuple([v * value for v in step])

    def add_v(step, step2):
        return tuple([v + step2[i] for i, v in enumerate(step)])

    return [add_v(begin, mul(step, r)) for r in range(WATER_GRADIENT)]


def render_shape(dc, shape):
    if shape.is_empty:
        return
    if isinstance(shape, MultiPolygon):
        for child in shape.geoms:
            render_shape(dc, child)
    if isinstance(shape, Polygon):
        dc.new_sub_path()
        for x, y in shape.exterior.coords:
            dc.line_to(x, y)
        dc.close_path()

def render_mark(dc, x, y):
    n = 8
    dc.move_to(x - n, y - n)
    dc.line_to(x + n, y + n)
    dc.move_to(x - n, y + n)
    dc.line_to(x + n, y - n)

def render_compass(dc):
    w, h = 4, 32
    dc.line_to(-w, 0)
    dc.line_to(0, h)
    dc.line_to(w, 0)
    dc.line_to(0, -h)
    dc.close_path()
    dc.set_source_rgb(*Color(hex='#FFFFFF').rgb)
    dc.set_line_width(4)
    dc.stroke_preserve()
    dc.fill()
    dc.line_to(-w, 0)
    dc.line_to(w, 0)
    dc.line_to(0, -h)
    dc.close_path()
    dc.set_source_rgb(*Color(hex='#DC3522').rgb)
    dc.fill()
    dc.save()
    dc.translate(0, -h * 3 / 2 - 8)
    w, h = 5, 15
    dc.line_to(-w, h)
    dc.line_to(-w, 0)
    dc.line_to(w, h)
    dc.line_to(w, 0)
    dc.set_source_rgb(*Color(hex='#FFFFFF').rgb)
    dc.stroke()
    dc.restore()

def render_curve(dc, points, alpha):
    items = zip(points, points[1:], points[2:], points[3:])
    # dc.line_to(*points[0])
    # dc.line_to(*points[1])
    for (x1, y1), (x2, y2), (x3, y3), (x4, y4) in items:
        a1 = math.atan2(y2 - y1, x2 - x1)
        a2 = math.atan2(y4 - y3, x4 - x3)
        cx = x2 + math.cos(a1) * alpha
        cy = y2 + math.sin(a1) * alpha
        dx = x3 - math.cos(a2) * alpha
        dy = y3 - math.sin(a2) * alpha
        dc.curve_to(cx, cy, dx, dy, x3, y3)
    # dc.line_to(*points[-1])

def find_path(layer, points, threshold, algo):
    x = layers.Noise(4, algo).add(layers.Constant(0.6)).clamp()
    x = x.translate(random.random() * 1000, random.random() * 1000)
    x = x.scale(0.01, 0.01)
    g = graph.make_graph(points, threshold, x)
    end = max(points, key=lambda p: layer.get(*p))
    points.sort(key=lambda p: math.hypot(p[0] - end[0], p[1] - end[1]))
    for start in reversed(points):
        path = graph.shortest_path(g, end, start)
        if path:
            return path

def render(algo = "simplex", method = "pyhull"):
    width = height = 512
    scale = 2
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24,
        width * scale, height * scale)
    dc = cairo.Context(surface)
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    dc.scale(scale, scale)
    layer = make_layer(algo)
    #layer.save('layer-' + algo + '.png', 0, 0, width, height)
    points = poisson_disc(0, 0, width, height, 8, 16)
    shape1 = layer.alpha_shape(points, 0.1, 1, 0.1, method).buffer(-4).buffer(4)
    shape2 = layer.alpha_shape(points, 0.3, 1, 0.1, method).buffer(-8).buffer(4)
    shape3 = layer.alpha_shape(points, 0.12, 0.28, 0.1, method).buffer(-12).buffer(4)
    points = [x for x in points
        if shape1.contains(Point(*x)) and layer.get(*x) >= 0.25]
    path = find_path(layer, points, 16, algo)
    mark = path[0]
    # water background
    dc.set_source_rgb(*Color(hex='#2185C5').rgb)
    dc.paint()
    # shallow water
    shape = shape1.simplify(8).buffer(32).buffer(-16)
    shapes = [shape]
    for _ in range(WATER_GRADIENT):
        shape = shape.simplify(8).buffer(64).buffer(-32)
        shape = xkcdify(shape, 2, 8)
        shapes.append(shape)
    shapes.reverse()
    c1 = Color(hex='#4FA9E1')
    c2 = Color(hex='#2185C5')
    for c, shape in zip(color_scale(c2.hsl, c1.hsl), shapes):
        dc.set_source_rgb(*(Color(hsl=c).rgb))
        render_shape(dc, shape)
        dc.fill()
    # height
    dc.save()
    dc.set_source_rgb(*Color(hex='#CFC291').rgb)
    for _ in range(5):
        render_shape(dc, shape1)
        dc.fill()
        dc.translate(0, 1)
    dc.restore()
    # sandy land
    dc.set_source_rgb(*Color(hex='#FFFFA6').rgb)
    render_shape(dc, shape1)
    dc.fill()
    # grassy land
    dc.set_source_rgb(*Color(hex='#BDF271').rgb)
    render_shape(dc, shape2)
    dc.fill()
    # dark sand
    dc.set_source_rgb(*Color(hex='#CFC291').rgb)
    render_shape(dc, shape3)
    dc.fill()
    # path
    dc.set_source_rgb(*Color(hex='#DC3522').rgb)
    render_curve(dc, path, 4)
    dc.set_dash([4])
    dc.stroke()
    dc.set_dash([])
    # mark
    dc.set_source_rgb(*Color(hex='#DC3522').rgb)
    render_mark(dc, *mark)
    dc.set_line_width(4)
    dc.stroke()
    # compass
    dc.save()
    dc.translate(48, height - 64)
    dc.rotate(random.random() * math.pi / 4 - math.pi / 8)
    render_compass(dc)
    dc.restore()
    return surface

if __name__ == '__main__':
    seed = 9
    random.seed(seed)
    surface = render()
    surface.write_to_png('out%02d.png' % seed)
    surface = render("snoise")
    surface.write_to_png('out%02d-b.png' % seed)
    surface = render("pnoise")
    surface.write_to_png('out%02d-c.png' % seed)
