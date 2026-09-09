# 开发日志：问题 · 解决 · 优化

记录本项目（Jazzy + gz Harmonic + TurtleBot3 + Cartographer + Nav2 实时建图导航）
从零到端到端跑通过程中遇到的坑、根因与修法，供复现与优化参考。

---

## A. 环境/选型层面
| # | 问题 | 根因 | 解决 / 优化 |
|---|---|---|---|
| A1 | 老教程用 Humble+Gazebo Classic，环境"不够典型"？ | Ubuntu 24.04 官方配 Jazzy；Humble 无 noble 官方包 | 不换环境：Jazzy + Harmonic 才是 Noble 的标准组合；TB3 用官方 Jazzy 维护版 2.3.x |
| A2 | "要不要下载 SLAM 算法" | — | 不用：cartographer/cartographer_ros/turtlebot3_cartographer 均系统已装，直接 include |
| A3 | SLAM 世界家具素材 | 本地无现成多功能厅/人模型 | 找到 gz 官方示例 actor(walk)，`gz fuel download` 缓存 Mingfei/actor；家具用 box 自建 |
| A4 | GUI 窗口打开后又整组退出 | 我的 sim.launch 给 GUI include 设了 `on_exit_shutdown:true`，且 world 里自加 `<gui>` 插件异常 | GUI 不设 on_exit_shutdown；world 去掉自定义 `<gui>` 段 |

## B. 打包/文件层面
| # | 问题 | 根因 | 解决 / 优化 |
|---|---|---|---|
| B1 | `model://lecture_hall` 找不到 | ament_python 的 `data_files` 用 glob 把 `models/lecture_hall/*.sdf` **拍平**安装到 `share/.../models/`（丢了子目录） | 写 `_install_tree()`：按相对路径**保留目录结构**安装 |
| B2 | gz 不解析自定义模型 | `GZ_SIM_RESOURCE_PATH` 没含我们 models 目录 | launch 内显式 `os.environ['GZ_SIM_RESOURCE_PATH']` 追加本包+官方 models（或 package.xml export `gazebo_model_path`） |
| B3 | `$(find-pkg-share …)` 不展开 | 直接 `parameters=[params_file]` 不经 RewrittenYaml | 直接把 bt xml 改成**绝对路径** |
| B4 | bash 命令莫名"被自杀"/中止 | 沙箱 bash 带 `-e`，且 `pkill -f` 匹配到自身命令行 | pkill 用 `[x]` 正则 + 每条 `|| true`；或按 pid kill |

## C. Nav2 联调（最曲折）
| # | 问题 | 根因 | 解决 / 优化 |
|---|---|---|---|
| C1 | lifecycle 反复"某节点 failed，Aborting bringup"，节点每次不同 | 官方 bringup 管太多节点（route/docking…）+重载下命令超时竞态 | 换**精简 launch**：只起 controller/planner/behavior/bt + 自管 lifecycle |
| C2 | bt_navigator 不 active：`Couldn't open input XML` | BT 需要 `behavior_server` 提供 spin/backup 恢复动作，未启动 → `Action server spin not available` | 补 `behavior_server` 节点并加入 lifecycle 名单 |
| C3 | `map` 与 `base_link` 是"两棵断开的树" | 我照抄了 nav2 的 `/tf→tf` 重映射（无命名空间时反而让 Nav2 看不到 gz /tf 动态 TF） | 去掉 tf 重映射（全局命名空间直接用 /tf） |
| C4 | global costmap **收不到 /map**（`no map received`） | costmap 进程实际在 `/global_costmap` 命名空间下；`map_topic:'map'` 相对名→`/global_costmap/map` | 改**绝对名 `map_topic: '/map'`**（关键！） |
| C5 | 发目标"瞬间成功"但不移动 / `Transform data too old` / `Extrapolation into the future` | **Nav2 节点没设 `use_sim_time`**：用墙钟(1.7e9s)而仿真 TF 用仿真钟(数百秒)，数量级错乱 | 每个 nav 节点 `use_sim_time: true`（总根源） |
| C6 | 目标在地图外被拒 / 直穿未建图椅阵 | global costmap 尺寸=静态图(小)或 unknown 全自由直穿 | global costmap 改**滚动 20×14m + allow_unknown**；再配合**分段目标**（中途点）推进式导航 |
| C7 | `transform_tolerance` 相关瞬时告警 | cartographer 静止时 map→odom 刷新间隔 vs 控制频率 | 将各 costmap/controller `transform_tolerance` 提到 1.0 |
| C8 | 大滚动 costmap 的 `width/height` 报类型错 | YAML 写 `20.0` 浮点 vs costmap 声明整型 | 写整型 `20/14` |

## D. 功能/算法设计优化
| 项 | 做法 | 理由 |
|---|---|---|
| 自动建图(巡游) | `patrol_node.py`：scan 驱动的反应式巡游（遇障朝开阔侧转、前移微调防贴墙、`--duration` 自停并报里程） | 无人值守可跑通建图；live 演示主流程无需 |
| 未知环境到远点 | **分段目标**（右通道前端 → 讲台），逐段 send `NavigateToPose` | 避免一次穿越大片未知区；每段距离<SLAM 感知/重规划尺度 |
| 定位方案 | 用 Cartographer 兼任定位（map→odom），不启 amcl/map_server | SLAM 实时建图即定位，避免两套 map→odom 冲突 |
| 目标坐标系 | map 原点=门口 spawn，goal 用 world−spawn 的相对坐标写进 `config/podium.yaml` | Cartographer 新图锚定起始位，坐标可直接换算 |
| 一键脚本 | `scripts/run_*.sh` 自动 source/export 后分段启动 | 演示零门槛 |

## E. 上位机 / 演示打磨（已落地）
- ✅ 上位机 RViz 总览：`/map` 实时地图 + RobotModel/TF 机器人 + `/lecture/markers`(红色圆柱=讲台、绿色球=路线点、文字=状态)
- ✅ **实时路线显示**：RViz 增加 Path 显示 —— `/plan`(绿色全局规划路线) 与 `/local_plan`(蓝色当前跟踪轨迹)；已验证二者在导航过程中发布
- ✅ 控制层节点 `lecture_control`：命令话题 `/lecture/cmd`(go/replan/stop/return)、取消 action=停车、新目标=重规划、`/lecture/status`(transient_local 持久，迟连也能读到)
- ✅ `stop_all.sh` 一并清理 rviz2 / host 进程
- 脚本 `run_00~06` + `DEMO_GUIDE.md` / `PROJECT_PLAN.md` / `DEVELOPMENT_LOG.md`

## F. 待办 / 下一步优化
- [x] **端到端回归工具**：`scripts/run_regression.sh`（无头自动 N 次跑"门口→讲台"，输出用时/成功/落点误差汇总）——偶发暴露了 SLAM 地图锚点漂移（个别 run 终点 map.y≈0 偏离讲台 ~3m，多数 run 精确到 ~0.02m），需进一步压制：候选＝启用 IMU 融合 A/B、或导航时减少移动 actor 干扰
- [ ] 把 yaml 中的绝对路径(bt xml)改为 launch 运行时展开，便于移植
- [ ] 巡游建图节点回归验证（功能已写，live 主流程不依赖）

## G. 优化前后对比与实测基线
### 关键修复（"能否跑通"）
| 阶段 | 现象 | 根因 | 结果 |
|---|---|---|---|
| 初版联调 | Nav2 反复 abort/节点状态乱跳 | 官方 bringup 节点过多 + 竞态 | 精简 launch（controller/planner/behavior/bt）自管生命周期 |
| 初版联调 | bt 不激活 | BT 需 behavior_server 的 spin/backup | 补 behavior_server |
| 初版联调 | 全局代价图收不到图 | costmap 在 `/global_costmap` 命名空间，`map_topic` 需绝对 `/map` | 改绝对名（关键） |
| 初版联调 | 发目标"瞬间完成"不动 | Nav2 未开 `use_sim_time`（墙钟 vs 仿真钟） | 各节点 `use_sim_time: true`（总根源） |
| 初版联调 | `/tf` 两棵树 | 多余 `/tf→tf` 重映射 | 去掉重映射 |
| 精度 | 早期成功 run 落点 0.1~1 m | 地图锚点漂移/回环弱 | 定制 `cartographer_lecture.lua`（提高回环优化频率、限定小厅回环距离）+ 分段导航 |

### 实测（headless 全流程计时，优化后）
| 指标 | 数值 |
|---|---|
| 到达用时 | ~35–50 s |
| 成功 run 落点误差 | ≈ 0.02 m（map 系 vs (5.3,-2.95)） |
| 偶发漂移 | 个别 run map.y 偏 ~3 m（候选对策见 §F） |
| 复测方式 | `scripts/run_regression.sh 5` |

### 可复现要点
1. 统一 `scripts/env.sh` 定位工作区；2. 每终端一条 `run_*.sh`；
3. 改参数后 `run_00_build.sh`；4. 地图/目标坐标见 `config/podium.yaml`（map 原点＝门口 spawn）。

## H. 2026-09-09：压住地图锚点漂移（实测 3.6m→0.24m）+ 回程诊断
### 触发：一次往返中"回程完全错乱"
- 现象：`go` 到讲台正常，`return` 后 **gz 物理真值离门口还有 ~5 m**，而 SLAM 却报 `ARRIVED`；RViz 地图有**重影/鬼影灰斑 + 墙错位**。
- 诊断（关键，避免以后再踩）：
  1. **gz 世界坐标系 ≠ map 帧**（有固定偏置），**不能直接比对 raw 坐标**。判漂移用两个无偏量：`map→odom` 起点→终点增幅，或 gz 真值 起点/终点差值（固定偏置自动抵消）。
  2. `map→odom` 增大**同时含**"轮式里程计累积误差被 SLAM 纠正"的正常部分，不能单独当漂移判据。
  3. 实测基线：新鲜建图起点 `map→odom ≈ (0.02,-0.02)`；跑完一趟往返后涨到 `(0.097,3.636) |T|≈3.6 m` —— 这就是锚点漂移。
- 根因：Cartographer 只吃 odometry+激光，**没开 IMU**；且回环优化距离/权重不足，抓不住"门口↔讲台↔门口"这种大闭环。

### 已实施修复（`config/cartographer_lecture.lua` + `launch/mapping.launch.py`，commit `0301ad3`）
| 项 | 改前→改后 | 意图 |
|---|---|---|
| `use_imu_data` | false→true | IMU 航向融合，抗偏航漂移 |
| `optimize_every_n_nodes` | 40→12 | 全局优化更频 |
| `global_sampling_ratio` | 0.003→0.02 | 更密全局约束 |
| `max_constraint_distance` | 4→6 | 让大闭环够得着 |
| `loop_closure_translation_weight` | 5→10 | 更信任闭环 |
| mapping.launch.py | +`imu_link→waffle_pi/imu_link/tb3_imu` 静态别名 | **必需**：gz 的 IMU 帧是模型前缀怪名，直接开 `use_imu_data` 会让 cartographer 查不到该帧而**卡死不再建图** |

### 实测（复测）
- 讲台到达：replan 后 `ARRIVED`，map 位姿 `(5.310,-2.920)`，误差 ≈**0.04 m**。
- 锚点：到讲台时 `map→odom` 停在 **0.24**（原 2.83）→ **漂移大幅压住**。
- 顿卦：首次 `go` 偶发在 `(5.27,-2.74)` 距讲台 0.2m 处 abort（`follow_path` 被 halt），`replan` 即稳定到达——属瞬时卡顿，非硬故障。

### 遗留：回程仍是**局部导航**问题（非 SLAM 漂移）
- 现象：`return` 在 gz `(4.26,4.44)`（约半途）失败，状态 `ERROR`；用户观察到"**回程扫不到座位且激光乱飘**"。
- Nav2 日志：`DWBLocalPlanner: No valid trajectories out of 819!` × 多 → `follow_path` abort。即**局部代价图被近场障碍四面围死**（scan 最近 0.12 m），DWB 无逃生轨迹。
- 地图采样：讲台→门口直线 **90% 空闲**，说明不是"假空墙"，而是机器人**窜入座椅/动态物体的密集近场**（激光被密集/飘移物体主导）。
- **候选下一步（未动）**：① 让 `return` 走"中途点→门口"同一走道，避免直穿座椅区；② 开启 Nav2 恢复行为(backup/spin)增强脱困；③ 评估 actor 鬼影对近场 costmap 的影响。这些属导航健壮性，与已压住的 SLAM 漂移分开处理。
