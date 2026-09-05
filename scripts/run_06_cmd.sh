#!/usr/bin/env bash
# 随时给机器人发命令（改最后的字符串即可）：
#   go / replan  -> 前往讲台(可随时重规划)   stop -> 立即停车   return -> 回门口
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
CMD="${1:-go}"
echo "send cmd: $CMD  (可选: go|replan|stop|return)"
ros2 topic pub --once /lecture/cmd std_msgs/msg/String "data: '$CMD'"
