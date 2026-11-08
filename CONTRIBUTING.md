# Contributing

- Metrics live in `nav_explore_eval/metrics.py` and are pure numpy: add a test in `test/test_metrics.py` with a synthetic grid, no ROS needed.
- Run `python3 -m pytest -q test` before opening a PR.
- Bump the version in `__init__.py`, `package.xml` and `setup.py` together and add a `CHANGELOG.md` entry.
- Keep commit messages short, one line.
