#!/usr/bin/env bash
# 端到端回归：无头自动跑 N 次「门口 → 讲台」，验收 成功率/用时/落点误差。
# 用法: ./scripts/run_regression.sh [次数，默认 3]
# 输出: 每次一行 + 汇总。全部成功且误差小 ⇒ 可放心交付。
N="${1:-3}"
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/env.sh"
TGT_X=5.30; TGT_Y=-2.95

fail(){ echo "   !! $1"; }
wait_scan(){
  for _ in $(seq 1 45); do
    if timeout 3 ros2 topic hz /scan 2>/dev/null | grep -q 'average rate'; then return 0; fi
    sleep 2
  done
  return 1
}
wait_map(){   # /map 为 1Hz，用 echo --once 读首帧，避免 hz 两帧门槛误判
  for _ in $(seq 1 45); do
    if timeout 6 ros2 topic echo /map --once 2>/dev/null | grep -q 'width:'; then return 0; fi
    sleep 2
  done
  return 1
}
wait_nav(){
  for _ in $(seq 1 40); do
    s=$(timeout 2 ros2 lifecycle get /bt_navigator 2>/dev/null)
    case "$s" in *active*) return 0;; esac
    sleep 2
  done
  return 1
}

echo "== 回归开始: ${N} 次 =="
OK=0
for i in $(seq 1 "$N"); do
  echo "--- 第 $i 次 ---"
  "$DIR/stop_all.sh" >/dev/null 2>&1; sleep 2
  LOG=/tmp/reg_sim.log;   ros2 launch tb3_lecture sim.launch.py gui:=false > "$LOG" 2>&1 & P_SIM=$!
  if ! wait_scan; then fail "仿真未就绪"; kill -9 $P_SIM 2>/dev/null; continue; fi
  LOG=/tmp/reg_slam.log; ros2 launch tb3_lecture mapping.launch.py use_rviz:=false patrol:=false > "$LOG" 2>&1 & P_SLAM=$!
  if ! wait_map; then fail "SLAM 未就绪"; "$DIR/stop_all.sh" >/dev/null 2>&1; continue; fi
  LOG=/tmp/reg_nav.log;  ros2 launch tb3_lecture live_nav.launch.py > "$LOG" 2>&1 & P_NAV=$!
  if ! wait_nav; then fail "Nav 未就绪"; "$DIR/stop_all.sh" >/dev/null 2>&1; continue; fi
  t0=$(date +%s)
  timeout 240 ros2 run tb3_lecture go_podium > /tmp/reg_go.log 2>&1
  rc=$?
  t1=$(date +%s)
  # 终点 map 位姿  (例: - Translation: [5.290, -2.966, -0.078])
  pose=$(timeout 5 ros2 run tf2_ros tf2_echo map base_footprint 2>/dev/null \
         | sed -n 's/.*\[\([-0-9.]*\), \([-0-9.]*\),.*/\1 \2/p' | head -1)
  read -r RX RY <<<"$pose" 2>/dev/null || RX=0; RY=0
  err=$(awk -v x="$RX" -v y="$RY" -v tx=$TGT_X -v ty=$TGT_Y \
        'BEGIN{printf "%.3f", sqrt((x-tx)^2 + (y-ty)^2)}')
  if [ "$rc" -eq 0 ]; then OK=$((OK+1)); st=成功; else st=失败; fi
  printf "  第%2d次: %s  用时=%ss  终点=(%.2f, %.2f)  误差=%sm\n" \
         "$i" "$st" "$((t1-t0))" "$RX" "$RY" "$err"
  "$DIR/stop_all.sh" >/dev/null 2>&1; sleep 2
done
echo "== 汇总: ${OK}/${N} 次成功 =="
[ "$OK" -eq "$N" ] && echo "全部成功 → 可交付基线通过。" || echo "存在失败 → 建议查日志 /tmp/reg_*.log"
