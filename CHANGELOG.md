# Changelog

## Unreleased

## 0.3.1
- **Fix:** `score map.yaml` read Nav2 `map_saver` output (unknown = grey 205 with `free_thresh: 0.25`) as free space, which inflated coverage by about 2x for saved maps. Trinary unknown now stays unknown (`mapio.load_yaml_map`). `record` and `bag` use `/map` messages and were not affected.
- Lint: no more `a; b` statements (flake8 clean), flake8 config in `setup.cfg`, `QUALITY_DECLARATION.md` (REP-2004 level 5).

## 0.3.0
- `bag`: score a rosbag2 offline (`/map` + `/odom` replayed in bag time).
- `record --repeat N --between CMD` and `stats`: repeat trials with mean ± std, grouped by label.
- `--rotate` / `--max-yaw`: auto-align now also searches a yaw offset.
- `truth-from-world`: nested models, `<include>` (`--model-path`, `$GAZEBO_MODEL_PATH`) and `.obj`/`.stl`/`.dae` meshes (as bounding boxes).
- `report`: one-file HTML report with coverage chart and map-vs-truth overlay.
- Multi-robot: `record --robots a,b` and `score-multi` give merged coverage, per-robot unique share and overlap.
- `leaderboard`, `validate`: `results/*.json` schema check and `LEADERBOARD.md` (CI keeps it fresh).
- `--gt-odom TOPIC` (record and bag): localisation error (`ate_rmse_m`, `ate_max_m`, `final_error_m`, `drift_pct`); `stats` adds an `ate_m` column.
- New metrics: `covered_area_m2`, `efficiency_m2_per_m`, `yaw_deg`.
- Packaging: extras, PyPI publish job (set repo variable `PUBLISH_PYPI=true`), Python 3.10/3.12 and Kilted CI.

## 0.2.0
- `truth-from-world`: exact ground-truth map from a Gazebo/SDF world (boxes and cylinders, flood-filled from the spawn point).

## 0.1.0
- `record` (live /map scoring), `score` (offline), `compare` (table + chart).
- Coverage, wall precision/recall/F1, false-free leak, time-to-percent, path length, FFT auto-align.
