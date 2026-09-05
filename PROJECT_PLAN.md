# 智能导航讲演台 —— 项目方案（具体实现）

> 目标：在 ROS 2 + Gazebo 仿真中，把 TurtleBot3 做成"智能讲演台"——
> 机器人从**侧门待机点**出发，在**没有预建地图**的环境里，用 **Cartographer 实时 SLAM 建图+定位**、
> **Nav2 规划避障**，自主行驶到**舞台前讲演位**；过程中支持**随时停车 / 重新规划**，
> 上位机实时显示地图、讲台位置、目标点与运行状态。

---

## 1. 系统环境（本机已验证）
| 项 | 值 |
|---|---|
| OS / ROS | Ubuntu 24.04 + **ROS 2 Jazzy** |
| 仿真 | **gz sim 8.10 (Gazebo Harmonic)**，桥 = `ros_gz`(bridge/sim/image) |
| SLAM | `cartographer_ros`(已装) + `turtlebot3_cartographer`(官方 lua 配置) |
| 导航 | Nav2 + `nav2_map_server`(map_saver 可选) |
| 机器人 | TurtleBot3 **Waffle Pi**（`TURTLEBOT3_MODEL=waffle_pi`） |
| 工程目录 | `~/tb3_lecture_ws`（colcon，ament_python 单包 `tb3_lecture`） |

## 2. 场景（校园多功能厅，见 `src/tb3_lecture/worlds/lecture_hall.world` + `models/lecture_hall/model.sdf`，由 `tools/gen_hall_sdf.py` 生成）
- 大厅内净 **10×8 m**，前端 +x 为舞台墙（投影幕+讲台桌），入口为**右侧墙后部侧门**。
- 观众区：中轴过道(y≈4.05)两侧各 **8 排、密集独立小椅**(每排 5/4 个) + **缓坡看台垫**（越靠后越高），贴右墙留 1.4 m 机器人通道。
- 两个走动的"参会人员"actor（Mingfei Actor，walk 动画，见 `world` 内 `<actor>`），模拟动态障碍。
- 前场舞台前放两座媒体柱作为绕行点缀。

**关键坐标（世界=world 系；SLAM 地图原点=门口 spawn）**
| 点 | world (x,y,yaw) | map/odom 相对 (x,y,yaw) |
|---|---|---|
| 侧门待机 spawn | (1.90, 7.00, 0°) | (0,0,0°) |
| 中途点（右通道前） | (6.70, 7.00, 0°) | (4.80, 0, 0°) |
| 讲演位 goal | (7.20, 4.05, 180°) | (5.30, -2.95, 180°) |

## 3. 架构与数据流
```
gz sim(世界+Waffle Pi+actor) ──ros_gz 桥──> /scan /odom /imu /clock /tf
        │
Cartographer(cartographer_node) 订阅 /scan /odom → 发 /map + TF map→odom(实时建图/定位)
        │
Nav2（精简：controller + planner + behavior + bt_navigator）
    global costmap(静态层=实时/map + 障碍层=/scan, 滚动 20×14m, allow_unknown)
    planner(Navfn) → 全局粗路径(可穿越未知区)
    controller(DWB) → 每秒多次采样的局部避障 → /cmd_vel → 底盘
        │
go_podium 节点：按【中途点→讲台】顺序发 /navigate_to_pose 目标
```

关键配置（`config/nav2_waffle_pi.yaml`，源自官方 TB3 参数改造）：
- `global_costmap`: `global_frame: map`、滚动窗口 20×14m、`static_layer.map_topic: "/map"`（**必须绝对名**，costmap 在 `/global_costmap` 命名空间下）、`map_subscribe_transient_local: true`（配 Cartographer 的 transient-local /map）。
- planner `GridBased.allow_unknown: true` —— 允许穿越尚未建图的区域（未知环境导航关键）。
- `bt_navigator.default_nav_to_pose_bt_xml` 为**绝对路径**（`$(find-pkg-share …)` 不会被直接喂参时展开）。
- 各 server/costmap `transform_tolerance: 1.0`。
- Nav2 各节点 **`use_sim_time: true`**（与仿真钟同步）。

**上位机（`host.launch.py`，RViz + `lecture_control`）实时显示**
- 地图：Cartographer `/map`（灰阶占据栅格，随建图扩张）
- 机器人位姿：TF / RobotModel；讲台目标与状态：`/lecture/markers`（红色圆柱=讲台、球=路线点、文字=状态）
- **路线：`/plan` 绿色全局规划路线 + `/local_plan` 蓝色当前跟踪轨迹**（RViz Path 显示）
- 控制：`/lecture/cmd` 命令话题（`go|replan|stop|return`），`/lecture/status` 状态话题

## 4. 启动流程（推荐 5 终端，均有脚本 `~/tb3_lecture_ws/scripts/run_*.sh`）
1. **仿真**：`run_01_sim.sh`（=`ros2 launch tb3_lecture sim.launch.py gui:=true`）
2. **实时 SLAM**：`run_02_slam.sh`（=`mapping.launch.py use_rviz:=false patrol:=false`）
3. **导航**：`run_03_nav.sh`（=`live_nav.launch.py`）
4. **上位机总览**：`run_05_host.sh`（=`host.launch.py` → RViz + lecture_control）
5. **出发/控制**：`run_06_cmd.sh go|stop|return|replan`
   或 `run_04_go.sh`（专用一键到讲台，不开 RViz）

> 每脚本已内置 source 与 export；手动敲命令则先 `source ~/tb3_lecture_ws/scripts/env.sh`。
> （可选）自动巡游建图：把第 2 步参数改 `patrol:=true`，另开 teleop 可手动兜底。

## 5. 说明与边界
- "一键直达"采用**分段目标**（先到右通道前端，再到讲台）：未知环境下一次规划穿越大片未建图区会直穿椅阵；分段让地图边推进边刷新，再由 Nav2 重规划第二段。两段均可随时被 Nav2 行为树按需重规划/恢复。
- 立即停车：取消当前 action（Ctrl-C go_podium / 发送新目标=重规划）。更完整的上位机控制（命令话题/状态话题/停车/重规划）见 `lecture_control`（后续阶段，若已实现则在此引用）。
- Cartographer 与 amcl **不可同时占用 map→odom**；本方案用 Cartographer 兼任定位，故不启动 map_server/amcl。

## 6. 实测基线与已知边界
> 数据来自 headless 全流程计时（门口→讲台，分两段），可随时用 `scripts/run_regression.sh N` 复测。

| 指标 | 实测 |
|---|---|
| 一次全流程到达用时 | 约 **35–50 s**（两段：右通道中途点 ~15–25 s + 讲台段 ~10–25 s，视地图/环境） |
| 成功落点精度（多数 run） | **≈ 0.02 m**（map 系位姿 vs 目标 (5.3, -2.95)） |
| 已知偶发 | 个别 run 出现 **SLAM 地图锚点漂移**（map 系落点 y 偏 ~3 m），多发生于建图受动态干扰/回环较弱时；候选对策：开 IMU 融合（`cartographer_lecture.lua` 一行）、或导航时移除移动 actor。回归工具即是为此类偶发问题提供量化手段 |

**已排障清单**（详见 DEVELOPMENT_LOG）：sim 时间未同步、costmap map_topic 需绝对 `/map`、多余 /tf 重映射、BT 依赖 behavior_server、`$(find-pkg-share)` 未展开、rolling 代价图边界等。
