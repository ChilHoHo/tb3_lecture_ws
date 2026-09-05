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
- [ ] 演员走位与机器人路径无交集校验；多次随机化起点回归测试
- [ ] 把 yaml 中的绝对路径(bt xml)改为 launch 运行时展开，便于移植
- [ ] 巡游建图节点回归验证（功能已写，live 主流程不依赖）
