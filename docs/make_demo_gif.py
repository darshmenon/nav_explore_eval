#!/usr/bin/env python3
"""Render docs/demo_run.json (a real `nav_explore_eval record` run) into docs/demo.gif."""
import io
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, 'demo_run.json')))
S = r['series']
T = [s['t'] for s in S]
COV = [s['coverage_pct'] for s in S]
BG, FG, ACC, DIM = '#16181e', '#d0d4dc', '#6edc82', '#78808c'


def frame(k):
    fig, (ax, tx) = plt.subplots(1, 2, figsize=(9, 3.9), gridspec_kw={'width_ratios': [3, 1.35]}, facecolor=BG)
    ax.set_facecolor(BG)
    ax.plot(T[:k + 1], COV[:k + 1], color=ACC, lw=2.4)
    ax.scatter([T[k]], [COV[k]], color=ACC, s=40, zorder=3)
    for p, t in r['time_to_pct_s'].items():
        if t is not None and t <= T[k]:
            ax.axhline(float(p), color=DIM, lw=0.8, ls=':')
            ax.annotate(f'{p}% at {t:.0f}s', (t, float(p)), xytext=(8, -14), textcoords='offset points', color=FG, fontsize=9)
    ax.set_xlim(0, max(T) * 1.02); ax.set_ylim(0, 60)
    ax.set_xlabel('time (s)', color=FG); ax.set_ylabel('coverage of explorable area (%)', color=FG)
    ax.tick_params(colors=FG)
    for sp in ax.spines.values():
        sp.set_color(DIM)
    ax.grid(alpha=0.15, color=FG)
    tx.axis('off'); tx.set_facecolor(BG)
    m = S[k]
    lines = [('time', f"{m['t']:.0f} s"), ('coverage', f"{m['coverage_pct']:.1f} %"), ('wall F1', f"{m['wall_f1_pct']:.1f} %"),
             ('false-free', f"{m['false_free_pct']:.1f} %"), ('frame offset', f"{m['dx_m']:.1f}, {m['dy_m']:.1f} m")]
    tx.text(0, 0.98, 'nav_explore_eval record', color=FG, fontsize=10, va='top', family='monospace')
    tx.text(0, 0.90, f"{r['label']}  vs  maze.world", color=DIM, fontsize=8.5, va='top', family='monospace')
    for i, (a, b) in enumerate(lines):
        y = 0.72 - i * 0.13
        tx.text(0, y, a, color=DIM, fontsize=10, family='monospace')
        tx.text(1.0, y, b, color=ACC if a == 'coverage' else FG, fontsize=11, ha='right', family='monospace')
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=80, facecolor=BG); plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('P', palette=Image.ADAPTIVE)


idx = list(range(0, len(S), 3)) + [len(S) - 1]
frames = [frame(k) for k in idx]
dur = [90] * len(frames)
dur[-1] = 3000
frames[0].save(os.path.join(HERE, 'demo.gif'), save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
print(len(frames), 'frames')
