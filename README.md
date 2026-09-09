# 智能导航讲演台 (tb3_lecture)

校园多功能厅仿真里，让 Waffle Pi **从侧门出发、无预建地图**，用 Cartographer 实时建图 + Nav2 自主导航开到**舞台讲演位**，并可**自主返回门口**。上位机 RViz 实时显示地图 / 路线 / 目标 / 状态，支持随时停车与重规划。

> 🎬 怎么跑 → [`DEMO_GUIDE.md`](DEMO_GUIDE.md) · &#128210; 方案 → [`PROJECT_PLAN.md`](PROJECT_PLAN.md)
> 📓 踩坑与修复 → [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md) · 🚚 打包部署 → [`INSTALL_NOTES.md`](INSTALL_NOTES.md) + `scripts/package_src.sh`

## 能力速览
- **无预建地图建图 + 自主导航**：Cartographer(实时 SLAM) 与 Nav2(规划避障) 并行，机器人从侧门自主开到讲台，再按"去程逆路线"自主返回门口。
- **场景**：程序生成的校园多功能厅（影院式密集座椅 + 缓坡看台 + 舞台 + 2 个走动演员），Waffle Pi 仿真。
- **上位机**：RViz 实时显示 地图 / 机器人 / 绿色全局规划路线 / 蓝色跟踪轨迹 / 讲台目标 / 状态文字。

## 实测基线（干净起点，完整往返）
| 指标 | 数值 |
|---|---|
| 门 → 讲台 | 用时 ~35–50 s，到达误差 ≈ **0.05 m** |
| 回程(end→门) | 物理误差 ≈ **0.23 m** |
| 定位一致性 | **map 与 gz 物理真值一致**（纯 gz 轮式里程计漂 ~7.8 m，由 SLAM + 闭环纠正回来） |
| 验收工具 | `scripts/run_regression.sh N` 自动跑 N 次并汇总成功率/用时/误差 |

> **稳定性修复（2026-09，见 DEVELOPMENT_LOG §H）**：开启 IMU 融合 + 加强全局闭环（`optimize_every_n_nodes 40→12`、`global_sampling_ratio →0.02`、`max_constraint_distance →6`、`loop_closure_translation_weight →10`），并让回程走"去程逆路线"、避免直线横穿座椅场——把"回程错乱"从偏 ~5 m / 卡死压到 ~0.23 m。

## 一键运行（5 个终端，各自运行一个脚本）
```bash
cd ~/tb3_lecture_ws/scripts
./run_01_sim.sh     # ① 仿真(GUI)
./run_02_slam.sh    # ② 实时 SLAM(Cartographer)
./run_03_nav.sh     # ③ 导航(Nav2)
./run_04_go.sh      # ④ 一键开到讲台
./run_05_host.sh    # ⑤ 上位机总览(RViz+控制)
# 随时控制: ./run_06_cmd.sh go|stop|return|replan
# 交付验收(无头自动回归N次到讲台): ./run_regression.sh 5
```

先跑一次 `./run_00_build.sh` 编译；每改世界 / 节点 / 配置后重跑编译。
> ⚠️ 改 `cartographer_lecture.lua` 后**一定重跑 `run_00_build.sh`**，配置从 install 目录加载。

## 目录速览
```
tb3_lecture_ws/
├── src/tb3_lecture/
│   ├── worlds/lecture_hall.world              # 多功能厅世界(含走动的 actor)
│   ├── models/lecture_hall/model.sdf          # 墙体/座椅/舞台(生成器产出)
│   ├── tools/gen_hall_sdf.py                  # 世界一键生成器
│   ├── launch/{sim,mapping,live_nav,host}.launch.py
│   ├── config/{cartographer_lecture.lua,      # SLAM 参数(IMU/闭环调优)
│   │           nav2_waffle_pi.yaml, podium.yaml}
│   ├── tb3_lecture/{patrol_node,go_podium,lecture_control}.py
│   └── rviz/tb3_lecture.rviz
├── scripts/run_*.sh                           # 一键脚本
└── PROJECT_PLAN.md / DEVELOPMENT_LOG.md / DEMO_GUIDE.md
```
