#!/usr/bin/env bash
# 终端1: 启动多功能厅仿真（Gazebo 窗口）。gui:=false 可无头跑。
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
ros2 launch tb3_lecture sim.launch.py gui:=true
