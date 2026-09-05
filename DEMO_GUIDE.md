# 演示操作手册 (DEMO_GUIDE)

> 项目：智能导航讲演台 —— TurtleBot3 + Cartographer 实时 SLAM + Nav2
> 一句话演示：**机器人从门口出发，在"没有预建地图"的环境里实时建图并自主导航到舞台讲台，再自主返回门口；全程 RViz 实时显示地图/机器人/目标/状态，随时可停车、重规划。**

前置阅读：[PROJECT_PLAN.md](PROJECT_PLAN.md)（方案）、[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)（技术难点）。

---

## 0. 一次性准备
```bash
~/tb3_lecture_ws/scripts/run_00_build.sh     # 编译（首次或改动后）
~/tb3_lecture_ws/scripts/stop_all.sh         # 如需清掉旧进程再重开
```
> 每个 run 脚本都已内置 source 环境，**无需手动 source**。

## 1. 启动整套流程（5 个终端，各 1 条，按顺序）
| 终端 | 命令 | 启动什么 / 你会看到 |
|---|---|---|
| A | `~/tb3_lecture_ws/scripts/run_01_sim.sh` | **Gazebo 仿真窗**：多功能厅全景，Waffle Pi 站在右侧门口通道，两个"人"在走动 |
| B | `~/tb3_lecture_ws/scripts/run_02_slam.sh` | **Cartographer 实时建图**（终端刷日志） |
| C | `~/tb3_lecture_ws/scripts/run_03_nav.sh` | **Nav2 导航**（4 节点 active） |
| D | `~/tb3_lecture_ws/scripts/run_05_host.sh` | **RViz 上位机**：实时地图 + 机器人 + 红色讲台圆柱 + 状态文字 IDLE |

启动后请确认 D 的 RViz 状态为 `lecture: IDLE`。

## 2. 演示动作
```bash
# 终端 E（或任意）：
~/tb3_lecture_ws/scripts/run_06_cmd.sh go      # ① 自主开往讲台
```
**看点（RViz / Gazebo）**：
1. 机器人沿右侧通道直线前移，**实时地图随它扩张**；
2. **绿色线 = 全局规划路线**（从门口连到讲台，随地图/障碍实时重画），车头附近**蓝色线 = 当前跟踪轨迹**（都在 RViz 里）；机器人沿绿色线行驶；
3. 到通道前端**转 90°** 进入中央过道、穿过观众座席区；
4. 停在**舞台正前讲演位**，状态变绿 **`ARRIVED`**（红色讲台圆柱上方文字）。

> 若看不到路线线：确认 RViz 左侧面板已勾选 “Global Plan” 与 “Local Plan”；或在导航进行中（非停车态）观察，规划路线只在行进时发布。

**随时互动（现场加分项）**：
```bash
~/tb3_lecture_ws/scripts/run_06_cmd.sh stop      # 立即停车（状态 STOPPED）
~/tb3_lecture_ws/scripts/run_06_cmd.sh go        # 继续 / 重新规划（可反复）
~/tb3_lecture_ws/scripts/run_06_cmd.sh return    # 自主返回门口
```

建议节奏：`go →（半路）stop → go → 到达 ARRIVED → return 回到门口`。

## 3. 说明 / 常见问题
- **坐标系**：导航以 map 帧为准；RViz 固定 Frame = map。判断"是否到讲台"看 RViz 里机器人是否贴合红色圆柱，或查状态 ARRIVED（地图位姿≈(5.3,-2.95)）。
- **没看到建图窗口**：实时地图在 **RViz**(run_05) 里看，不是 Gazebo。
- **仿真偏慢/偏卡**：Gazebo 世界部件较多，可把 `run_01_sim.sh` 中 `gui:=true` 改 `false`（无仿真窗更流畅，主要看 RViz 即可）。
- **想手动开地图模式（自动巡游建图）**：
  ```bash
  ~/tb3_lecture_ws/scripts/run_02_slam.sh        # 改成 patrol:=true 参数可自动巡游
  ```
- **想一键去讲台（不靠上位机控制）**：终端 E 用 `~/tb3_lecture_ws/scripts/run_04_go.sh`。

## 4. 环境速查
```bash
# 若想在脚本外手动敲命令，先：
source ~/tb3_lecture_ws/scripts/env.sh
ros2 topic pub --once /lecture/cmd std_msgs/msg/String "data: 'go'"   # 等价 run_06
```
主题/服务：`/map`(Cartographer实时图)、`/scan`、`/odom`、`/navigate_to_pose`(Nav2 action)、`/lecture/cmd`(命令)、`/lecture/status`(状态)、`/lecture/markers`(目标/状态可视化)。
