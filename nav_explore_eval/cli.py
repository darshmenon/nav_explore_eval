#!/usr/bin/env python3
"""nav_explore_eval - score any exploration run on coverage, map accuracy and time-to-percent."""
import argparse
import json
import sys
import time

from . import __version__
from .mapio import load_yaml_map
from .metrics import TIME_TO, align, path_length, score, time_to_percent


def cmd_score(a):
    live, truth = load_yaml_map(a.map), load_yaml_map(a.truth)
    dx, dy = (a.offset if a.offset else (align(live, truth, a.max_shift) if a.align else (0.0, 0.0)))
    res = score(live, truth, dx, dy, a.tol)
    print(json.dumps(res, indent=2) if a.json else '\n'.join(f'{k:20s} {v:8.2f}' for k, v in res.items()))
    return 0


def _row(path):
    r = json.load(open(path))
    f, tt = r['final'], r['time_to_pct_s']
    return [r['label'], f"{f['coverage_pct']:.1f}", f"{f['wall_f1_pct']:.1f}", f"{f['false_free_pct']:.1f}",
            f"{r['path_length_m']:.1f}"] + [('-' if tt[str(p)] is None else f'{tt[str(p)]:.0f}') for p in TIME_TO]


def cmd_compare(a):
    head = ['label', 'cov%', 'f1%', 'leak%', 'path_m'] + [f't{p}%(s)' for p in TIME_TO]
    rows = [head] + [_row(p) for p in a.reports]
    w = [max(len(r[i]) for r in rows) for i in range(len(head))]
    for r in rows:
        print('  '.join(c.rjust(w[i]) for i, c in enumerate(r)))
    if a.png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        for p in a.reports:
            r = json.load(open(p))
            ax.plot([s['t'] for s in r['series']], [s['coverage_pct'] for s in r['series']], label=r['label'])
        ax.set_xlabel('time (s)'); ax.set_ylabel('coverage (%)'); ax.legend(); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(a.png, dpi=140)
        print(f'wrote {a.png}')
    return 0


def cmd_record(a, ros_args):
    import rclpy
    from nav_msgs.msg import OccupancyGrid, Odometry
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
    from .mapio import from_msg

    rclpy.init(args=ros_args)
    node = Node('nav_explore_eval')
    truth = load_yaml_map(a.truth)
    state = {'map': None, 'pts': [], 'series': [], 'off': (0.0, 0.0), 'final': None}
    t0 = time.monotonic()
    ns = ('/' + a.ns.strip('/')) if a.ns else ''
    node.create_subscription(OccupancyGrid, f'{ns}/map', lambda m: state.__setitem__('map', from_msg(m)),
                             QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def on_odom(m):
        p = m.pose.pose.position
        if not state['pts'] or abs(p.x - state['pts'][-1][0]) + abs(p.y - state['pts'][-1][1]) > 0.02:
            state['pts'].append((p.x, p.y))
    node.create_subscription(Odometry, f'{ns}/odom', on_odom, qos_profile_sensor_data)

    def tick():
        t = time.monotonic() - t0
        if state['map'] is None:
            if t >= a.duration:
                raise SystemExit
            return
        state['off'] = align(state['map'], truth, a.max_shift) if a.align else (0.0, 0.0)
        m = score(state['map'], truth, *state['off'], a.tol)
        state['series'].append((t, m)); state['final'] = m
        node.get_logger().info(f't={t:5.0f}s coverage={m["coverage_pct"]:.1f}% f1={m["wall_f1_pct"]:.1f}%')
        if t >= a.duration or m['coverage_pct'] >= a.stop_at:
            raise SystemExit
    node.create_timer(a.interval, tick)
    from rclpy.executors import ExternalShutdownException
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit, ExternalShutdownException):
        pass
    node.destroy_node(); rclpy.try_shutdown()
    if not state['series']:
        print('no /map received - nothing to score', file=sys.stderr)
        return 1
    rep = {'label': a.label, 'truth': a.truth, 'duration_s': state['series'][-1][0],
           'path_length_m': path_length(state['pts']), 'final': state['final'],
           'time_to_pct_s': time_to_percent(state['series']),
           'series': [dict(t=t, **m) for t, m in state['series']]}
    json.dump(rep, open(a.out, 'w'), indent=2)
    print(f'wrote {a.out}')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='nav_explore_eval', description=__doc__)
    ap.add_argument('--version', action='version', version=f'nav_explore_eval {__version__}')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('score', help='score a saved map against a ground-truth map (offline)')
    s.add_argument('map'); s.add_argument('truth')
    s.add_argument('--align', action='store_true', help='auto-find the translation between map frames')
    s.add_argument('--offset', type=float, nargs=2, metavar=('DX', 'DY'))
    s.add_argument('--max-shift', type=float, default=3.0)
    s.add_argument('--tol', type=float, default=0.10, help='wall match tolerance in metres')
    s.add_argument('--json', action='store_true')
    c = sub.add_parser('compare', help='table (and chart) comparing recorded runs')
    c.add_argument('reports', nargs='+'); c.add_argument('--png')
    r = sub.add_parser('record', help='watch a live /map and score it over time')
    r.add_argument('--truth', required=True, help='ground-truth map yaml')
    r.add_argument('--label', default='run'); r.add_argument('--out', default='run.json')
    r.add_argument('--ns', default=''); r.add_argument('--duration', type=float, default=600)
    r.add_argument('--stop-at', type=float, default=100.0, help='stop when coverage %% reached')
    r.add_argument('--interval', type=float, default=2.0)
    r.add_argument('--align', action='store_true'); r.add_argument('--max-shift', type=float, default=3.0)
    r.add_argument('--tol', type=float, default=0.10, help='wall match tolerance in metres')
    a, ros_args = ap.parse_known_args(argv)
    if a.cmd == 'score':
        return cmd_score(a)
    if a.cmd == 'compare':
        return cmd_compare(a)
    return cmd_record(a, ros_args)


if __name__ == '__main__':
    raise SystemExit(main())
