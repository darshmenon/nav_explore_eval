# nav_explore_eval

[![CI](https://github.com/darshmenon/nav_explore_eval/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darshmenon/nav_explore_eval/actions/workflows/ci.yml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%20%7C%20Jazzy-blue)](https://docs.ros.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

How good was that exploration run? Score any ROS 2 exploration against a ground-truth map: coverage, wall accuracy, and time to 25/50/75/90 %.

```bash
# ground truth straight from a Gazebo world file (no SLAM run needed)
ros2 run nav_explore_eval nav_explore_eval truth-from-world maze.world --out maze_truth --seed 0 0

# live: watch /map while any explorer runs, write a JSON report
ros2 run nav_explore_eval nav_explore_eval record --truth truth.yaml --label explore_lite --out lite.json --align

# offline: score a saved map
ros2 run nav_explore_eval nav_explore_eval score map.yaml truth.yaml --align

# compare runs side by side (+ optional chart)
ros2 run nav_explore_eval nav_explore_eval compare lite.json frontier.json --png compare.png
```

```
   label  cov%   f1%  leak%  path_m  t25%(s)  t50%(s)  t75%(s)  t90%(s)
    lite  91.2  88.0    1.1   412.0       41       95      180      340
frontier  96.8  90.5    0.7   388.5       35       70      130      210
```

## Why

Exploration papers and packages each report different numbers. This tool gives one scoring method that works with any explorer, any SLAM and any robot, because it only watches `/map` and `/odom`.

- **Coverage**: share of the ground-truth free space the map has marked free.
- **Wall F1 / leak**: wall precision and recall within a tolerance (`--tol`, default 0.10 m), and the share of real walls the map shows as free.
- **Auto-align** (`--align`): SLAM maps start at the robot, not the truth map's origin, so the tool finds the translation between the two frames by FFT correlation of the walls.
- **Time-to-percent**: interpolated time to reach each coverage level, plus path length from `/odom`.

Align is translation-only: a SLAM run that is rotated against the truth map needs `--offset` or a re-saved map. Maps from two different SLAM runs of the same world can score low on wall F1 even when they look alike, so raise `--tol` when comparing runs.

- **Ground truth from the world file** (`truth-from-world`): rasterises the box and cylinder collisions that cross the lidar height, and counts as explorable only the free space reachable from `--seed` (the robot spawn). Walls, ramps and furniture below `--z` are ignored; meshes are not supported yet.

Build: `colcon build --packages-select nav_explore_eval`. Tests: `python3 -m pytest test` (the live `record` tests run when ROS 2 is sourced).
