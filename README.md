# nav_explore_eval

[![CI](https://github.com/darshmenon/nav_explore_eval/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darshmenon/nav_explore_eval/actions/workflows/ci.yml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%20%7C%20Jazzy-blue)](https://docs.ros.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**How good was that exploration run?** Score any ROS 2 exploration against a ground-truth map: coverage, wall accuracy, and time to 25 / 50 / 75 / 90 %. It only watches `/map` and `/odom`, so it works with any explorer, any SLAM and any robot.

![Coverage of the explorable area growing over a 7-minute run, with wall F1 and false-free live](docs/demo.gif)

*A real 7-minute run: `explore:=true` on a Gazebo maze, scored against the exact ground truth built from the world file. Data: `docs/demo_run.json`, renderer: `docs/make_demo_gif.py`.*

Built alongside [rosnav](https://github.com/darshmenon/rosnav), a ROS 2 Nav2 stack with SLAM, frontier exploration and multi-robot fleets, and run on its Gazebo maze sim.

## Quick start

```bash
# 1. exact ground truth from your Gazebo world (no SLAM run needed); --seed = robot spawn
ros2 run nav_explore_eval nav_explore_eval truth-from-world maze.world --out maze_truth --seed 0 0

# 2. start your explorer as usual, then score it live (writes a JSON report at the end)
ros2 run nav_explore_eval nav_explore_eval record --truth maze_truth.yaml --label my_explorer --out run.json --align

# 3. compare runs side by side, optional chart
ros2 run nav_explore_eval nav_explore_eval compare run.json other.json --png compare.png

# or score a map you already saved
ros2 run nav_explore_eval nav_explore_eval score map.yaml maze_truth.yaml --align
```

Real output of the run above:

```
       label  cov%   f1%  leak%  path_m  t25%(s)  t50%(s)  t75%(s)  t90%(s)
builtin_maze  43.8  64.1    0.0    15.9      158        -        -        -
```

## What it measures

| Metric | Meaning |
|---|---|
| `coverage` | share of the **explorable** free space (reachable from the spawn point) the map has marked free |
| `wall F1` | precision and recall of wall cells within `--tol` metres (default 0.10) |
| `leak` (false-free) | share of real wall cells the map shows as free space, which is the dangerous error |
| `t25 … t90` | interpolated time to reach each coverage level (`-` = never reached) |
| `path_m` | distance driven, from `/odom` |

- **Auto-align** (`--align`): a SLAM map starts at the robot, not at the truth map's origin, so the tool finds the translation between the two frames by FFT correlation of the walls (the run above found a 1.5 m, 0.9 m offset).
- **Ground truth from the world file**: rasterises the box and cylinder collisions that cross the lidar height (`--z`) and counts only space reachable from `--seed` as explorable, so sealed-off rooms and the outside never count against you.

## More commands

```bash
# score a recorded rosbag2 offline (no live sim needed)
nav_explore_eval bag my_bag/ --truth maze_truth.yaml --label run1 --out run1.json --align

# repeat trials (restart the explorer before each), then mean +/- std grouped by label
nav_explore_eval record --truth maze_truth.yaml --label A --out results/A.json --align --repeat 5 --between ./restart.sh
nav_explore_eval stats results/

# one-file HTML report; add --map/--truth for the map-vs-truth overlay (leaks in red)
nav_explore_eval report results/ --out report.html --map slam_map.yaml --truth maze_truth.yaml

# multi-robot: merged coverage, each robot's unique share, overlap
nav_explore_eval record --robots robot1,robot2 --truth maze_truth.yaml --align
nav_explore_eval score-multi r1.yaml r2.yaml --truth maze_truth.yaml

# localisation error: compare /odom with a ground-truth Odometry topic (works for record and bag)
nav_explore_eval record --truth maze_truth.yaml --gt-odom /ground_truth/odom --align
nav_explore_eval bag my_bag/ --truth maze_truth.yaml --gt-odom /ground_truth/odom

# rotated SLAM frame: also search yaw
nav_explore_eval score map.yaml maze_truth.yaml --rotate
```

Extra run metrics: `covered_area_m2` and `efficiency_m2_per_m` (area explored per metre driven).
See [`LEADERBOARD.md`](LEADERBOARD.md) to compare runs; add yours as `results/<name>.json` in a pull request (`nav_explore_eval validate` checks it).
Combining with fault injection: [docs/integrations.md](docs/integrations.md).

## Limits

- Yaw search is a coarse grid (`--max-yaw`, 1 degree steps) about the world origin, and it multiplies align time.
- `truth-from-world` reads boxes, cylinders and meshes (as bounding boxes, so concave meshes are filled in); heightmaps and `<polyline>` are skipped with a warning.
- Two SLAM runs of the same world can score low on wall F1 even when they look alike. Raise `--tol` when comparing runs against each other, and prefer a world-file truth.
- Multi-robot assumes all maps share one frame (each is aligned to the truth separately).
- Localisation error (ATE) pairs poses by nearest time within 0.25 s and rigidly fits the trajectory first, so it measures drift, not frame offset. It compares `/odom` to your ground-truth topic.

## Roadmap

- true polygon footprints for meshes
- more entries on the leaderboard

Build: `colcon build --packages-select nav_explore_eval`. Tests: `python3 -m pytest test` (the live `record` tests run when ROS 2 is sourced). Part of a set with [nav2_doctor](https://github.com/darshmenon/nav2_doctor) and [nav2_fault_inject](https://github.com/darshmenon/nav2_fault_inject).
