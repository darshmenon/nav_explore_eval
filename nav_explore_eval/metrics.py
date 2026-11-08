"""Exploration metrics: coverage, map accuracy, time-to-percent. Pure numpy, no ROS."""
import numpy as np

from .mapio import Grid

TIME_TO = (25, 50, 75, 90)


def resample(live: Grid, truth: Grid, dx=0.0, dy=0.0):
    """Nearest-neighbour live -> truth grid, live shifted by (dx, dy) metres. Outside live = unknown."""
    h, w = truth.shape
    ys = truth.oy + (np.arange(h) + 0.5) * truth.resolution - dy
    xs = truth.ox + (np.arange(w) + 0.5) * truth.resolution - dx
    j = np.floor((xs - live.ox) / live.resolution).astype(int)
    i = np.floor((ys - live.oy) / live.resolution).astype(int)
    out = np.full((h, w), -1, dtype=np.int8)
    ok_i = (i >= 0) & (i < live.shape[0]); ok_j = (j >= 0) & (j < live.shape[1])
    out[np.ix_(ok_i, ok_j)] = live.data[np.ix_(i[ok_i], j[ok_j])]
    return out


def _dilate(m, r=1):
    out = m.copy()
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out |= np.roll(np.roll(m, di, 0), dj, 1)
    return out


def align(live: Grid, truth: Grid, max_shift_m=3.0):
    """Best (dx, dy) in metres that overlays live walls on truth walls (translation only)."""
    a = resample(live, truth) == 100
    b = truth.data == 100
    if a.sum() < 10 or b.sum() < 10:
        return 0.0, 0.0
    h, w = b.shape
    F = np.fft.rfft2(b.astype(float), s=(2 * h, 2 * w))
    G = np.fft.rfft2(a.astype(float), s=(2 * h, 2 * w))
    c = np.fft.irfft2(F * np.conj(G), s=(2 * h, 2 * w))     # c[s] = sum b[x+s] * a[x]
    ms = int(max_shift_m / truth.resolution)
    best, bs = -1.0, (0, 0)
    for si in range(-ms, ms + 1):
        row = c[si % (2 * h)]
        for sj in range(-ms, ms + 1):
            v = row[sj % (2 * w)]
            if v > best:
                best, bs = v, (si, sj)
    return bs[1] * truth.resolution, bs[0] * truth.resolution


def score(live: Grid, truth: Grid, dx=0.0, dy=0.0, tol_m=0.10):
    """Coverage + accuracy of `live` vs ground-truth `truth` after shifting live by (dx, dy).
    A wall cell matches a wall within `tol_m` metres."""
    tol_cells = max(0, int(round(tol_m / truth.resolution)))
    r = resample(live, truth, dx, dy)
    t_free, t_occ = truth.data == 0, truth.data == 100
    l_free, l_occ = r == 0, r == 100
    coverage = (l_free & t_free).sum() / max(t_free.sum(), 1) * 100
    wall_cov = (_dilate(l_occ, tol_cells) & t_occ).sum() / max(t_occ.sum(), 1) * 100   # recall
    prec = (l_occ & _dilate(t_occ, tol_cells)).sum() / max(l_occ.sum(), 1) * 100
    f1 = 2 * prec * wall_cov / max(prec + wall_cov, 1e-9)
    leak = (l_free & t_occ & ~_dilate(l_occ, tol_cells)).sum() / max(t_occ.sum(), 1) * 100
    return {'coverage_pct': float(coverage), 'wall_recall_pct': float(wall_cov),
            'wall_precision_pct': float(prec), 'wall_f1_pct': float(f1),
            'false_free_pct': float(leak), 'dx_m': float(dx), 'dy_m': float(dy)}


def time_to_percent(series, key='coverage_pct', targets=TIME_TO):
    """series = [(t, metrics_dict)] ascending in t. Linear-interpolated first crossing, else None."""
    out = {}
    for p in targets:
        out[str(p)] = None
        prev = None
        for t, m in series:
            v = m[key]
            if v >= p:
                if prev is None or v == prev[1]:
                    out[str(p)] = float(t)
                else:
                    out[str(p)] = float(prev[0] + (t - prev[0]) * (p - prev[1]) / (v - prev[1]))
                break
            prev = (t, v)
    return out


def path_length(points):
    p = np.asarray(points, dtype=float)
    return float(np.hypot(*np.diff(p, axis=0).T).sum()) if len(p) > 1 else 0.0
