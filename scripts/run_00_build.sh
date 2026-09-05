#!/usr/bin/env bash
# 编译工程（改完世界/launch/节点后重跑）
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
cd "$WS_ROOT"
colcon build --packages-select tb3_lecture
echo "build done. 现在用 scripts/run_01_sim.sh 等启动。"
