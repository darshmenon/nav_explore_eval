# Using nav_explore_eval with nav2_fault_inject and nav2_doctor

Score how an explorer copes with a failure: freeze a node mid-run, then compare against a clean run.

```bash
# clean baseline, 3 trials (--between restarts your explorer before each one)
ros2 run nav_explore_eval nav_explore_eval record --truth maze_truth.yaml --label clean \
  --out results/clean.json --align --repeat 3 --between './restart_explorer.sh'

# same, but freeze the sim bridge for 8 s at t=20 s of every trial (start the injector inside --between)
ros2 run nav_explore_eval nav_explore_eval record --truth maze_truth.yaml --label bridge_hang \
  --out results/bridge_hang.json --align --repeat 3 \
  --between './restart_explorer.sh; ros2 run nav2_fault_inject nav2_fault_inject run scenario.yaml &'

ros2 run nav_explore_eval nav_explore_eval stats results     # mean +/- std per label
ros2 run nav_explore_eval nav_explore_eval report results --out report.html
```

Run `nav2_doctor` beside it to see which check fired while the coverage curve flattened; both tools
print wall-clock times, so the logs line up.

Status: the commands above use only documented flags of each tool, but this exact combined recipe has
not been run end to end yet.
