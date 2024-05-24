import random
from math import hypot, sqrt

from pyhull.delaunay import DelaunayTri
from shapely.geometry import MultiPoint,MultiLineString
from shapely.ops import polygonize, triangulate, unary_union

def alpha_shape(initial_points, alpha, method="pyhull"):
    def add_edge(points, i, j):
        if (i, j) in edges or (j, i) in edges:
            return
        edges.add((i, j))
        edge_points.append((points[i], points[j]))

    if method == "shapely":
        shapes = triangulate(MultiPoint(initial_points), tolerance=0.001)
    else:
        tri = DelaunayTri(initial_points)
        vertices = tri.vertices
        points = tri.points
        edges = set()
        edge_points = []
        for i1, i2, i3 in vertices:
            x1, y1 = points[i1]
            x2, y2 = points[i2]
            x3, y3 = points[i3]
            a = hypot(x1 - x2, y1 - y2)
            b = hypot(x2 - x3, y2 - y3)
            c = hypot(x3 - x1, y3 - y1)
            s = (a + b + c) / 2.0
            area = sqrt(s * (s - a) * (s - b) * (s - c))
            if ((a * b * c) / area) < alpha:
                add_edge(points, i1, i2)
                add_edge(points, i2, i3)
                add_edge(points, i3, i1)
        shapes = list(polygonize(MultiLineString(edge_points)))
    return unary_union(shapes)
