#!/usr/bin/env bash
# 终端4: 一键「去讲台」（分两段：通道前端中途点 → 讲演位）
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
ros2 run tb3_lecture go_podium
