"""Exact ground-truth occupancy map from a Gazebo/SDF world: rasterise box and cylinder collisions."""
import math
import re
import xml.etree.ElementTree as ET
from collections import deque

import numpy as np

from .mapio import Grid


def _pose(el):
    """(x, y, yaw) from a <pose> child; roll/pitch are ignored (walls are upright)."""
    p = el.find('pose') if el is not None else None
    v = [float(t) for t in (p.text or '').split()] if p is not None and p.text else []
    v += [0.0] * (6 - len(v))
    return v[0], v[1], v[5], v[2]


def _compose(a, b):
    (ax, ay, ayaw), (bx, by, byaw) = a, b
    c, s = math.cos(ayaw), math.sin(ayaw)
    return ax + c * bx - s * by, ay + s * bx + c * by, ayaw + byaw


def shapes(world_text, z=0.2):
    """[(kind, cx, cy, yaw, dims)] for collisions that intersect the horizontal plane at height `z`."""
    root = ET.fromstring(re.sub(r'<\?xml[^>]*\?>', '', world_text).strip())
    out = []
    for model in root.iter('model'):
        mx, my, myaw, mz = _pose(model)
        for link in model.findall('link'):
            lx, ly, lyaw, lz = _pose(link)
            for col in link.findall('collision'):
                cx, cy, cyaw, cz = _pose(col)
                geo = col.find('geometry')
                if geo is None:
                    continue
                x, y, yaw = _compose(_compose((mx, my, myaw), (lx, ly, lyaw)), (cx, cy, cyaw))
                zc = mz + lz + cz
                box, cyl = geo.find('box/size'), geo.find('cylinder')
                if box is not None:
                    sx, sy, sz = (float(t) for t in box.text.split())
                    if abs(z - zc) <= sz / 2:
                        out.append(('box', x, y, yaw, (sx, sy)))
                elif cyl is not None:
                    r, h = float(cyl.findtext('radius')), float(cyl.findtext('length'))
                    if abs(z - zc) <= h / 2:
                        out.append(('cyl', x, y, yaw, (r,)))
    return out


def rasterize(shape_list, res=0.05, margin=1.0, seed=(0.0, 0.0)):
    """Grid: 100 walls, 0 free space reachable from `seed`, -1 everything else (outside the walls)."""
    if not shape_list:
        raise ValueError('no collision shapes at that height - check --z or the world file')
    xs_, ys_ = [], []
    for kind, x, y, yaw, d in shape_list:
        if kind == 'box':
            hx = abs(math.cos(yaw)) * d[0] / 2 + abs(math.sin(yaw)) * d[1] / 2
            hy = abs(math.sin(yaw)) * d[0] / 2 + abs(math.cos(yaw)) * d[1] / 2
        else:
            hx = hy = d[0]
        xs_ += [x - hx, x + hx]; ys_ += [y - hy, y + hy]
    x0, x1, y0, y1 = min(xs_) - margin, max(xs_) + margin, min(ys_) - margin, max(ys_) + margin
    w, h = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    xs = x0 + (np.arange(w) + 0.5) * res
    ys = y0 + (np.arange(h) + 0.5) * res
    X, Y = np.meshgrid(xs, ys)
    occ = np.zeros((h, w), dtype=bool)
    for kind, cx, cy, yaw, d in shape_list:
        dx, dy = X - cx, Y - cy
        c, s = math.cos(-yaw), math.sin(-yaw)
        u, v = c * dx - s * dy, s * dx + c * dy
        occ |= (np.abs(u) <= d[0] / 2) & (np.abs(v) <= d[1] / 2) if kind == 'box' else (dx * dx + dy * dy <= d[0] ** 2)
    grid = np.full((h, w), -1, dtype=np.int8)
    si, sj = int((seed[1] - y0) / res), int((seed[0] - x0) / res)
    if not (0 <= si < h and 0 <= sj < w) or occ[si, sj]:
        raise ValueError(f'seed {seed} is outside the world or inside a wall - pass --seed X Y in free space')
    seen = np.zeros_like(occ)
    q = deque([(si, sj)]); seen[si, sj] = True
    while q:
        i, j = q.popleft()
        for ni, nj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= ni < h and 0 <= nj < w and not seen[ni, nj] and not occ[ni, nj]:
                seen[ni, nj] = True
                q.append((ni, nj))
    grid[seen] = 0
    walls = occ & _touches(seen)                     # keep only walls that bound the explorable space
    grid[walls] = 100
    return Grid(grid, res, x0, y0)


def _touches(m):
    out = m.copy()
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        out |= np.roll(np.roll(m, di, 0), dj, 1)
    return out


def write_map(grid, prefix):
    """prefix.pgm + prefix.yaml in map_server format (free 254, occupied 0, unknown 205)."""
    img = np.where(grid.data == 100, 0, np.where(grid.data == 0, 254, 205)).astype(np.uint8)[::-1]
    with open(prefix + '.pgm', 'wb') as f:
        f.write(b'P5\n%d %d\n255\n' % (img.shape[1], img.shape[0]) + img.tobytes())
    name = prefix.rsplit('/', 1)[-1]
    with open(prefix + '.yaml', 'w') as f:
        f.write(f'image: {name}.pgm\nresolution: {grid.resolution}\norigin: [{grid.ox:.3f}, {grid.oy:.3f}, 0.0]\n'
                'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
