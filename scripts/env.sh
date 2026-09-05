#!/usr/bin/env bash
# 环境初始化（可移植：自动定位工作区，不写死 HOME 路径）
# 用法：source env.sh  （或每个 run_*.sh 已内置）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export WS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"     # 工作区根目录
export TURTLEBOT3_MODEL=waffle_pi
source /opt/ros/jazzy/setup.bash
if [ -f "$WS_ROOT/install/setup.bash" ]; then
  source "$WS_ROOT/install/setup.bash"
else
  echo "[env] 未找到 $WS_ROOT/install/setup.bash —— 请先运行 scripts/run_00_build.sh"
fi
