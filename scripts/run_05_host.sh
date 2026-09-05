#!/usr/bin/env bash
# 上位机总览：RViz(地图/机器人/目标/状态) + lecture_control(go/stop/replan/return)
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
ros2 launch tb3_lecture host.launch.py
