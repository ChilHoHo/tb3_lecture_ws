#!/usr/bin/env bash
# 终端3: 实时导航（Nav2 精简栈：controller/planner/behavior/bt）
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
ros2 launch tb3_lecture live_nav.launch.py
