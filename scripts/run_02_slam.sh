#!/usr/bin/env bash
# 终端2: 实时 SLAM（Cartographer 建图+定位，无预建地图）
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
ros2 launch tb3_lecture mapping.launch.py use_rviz:=false patrol:=false
