# 智能导航讲演台 (TurtleBot3 + Cartographer 实时 SLAM + Nav2)

校园多功能厅仿真里，让 Waffle Pi 从**侧门**出发，在**没有预建地图**的情况下实时建图并
自主导航到**舞台讲演位**；上位机 RViz 实时显示地图/讲台位置/目标点/状态，支持随时停车与重规划。

> 🎬 **演示怎么跑** → [`DEMO_GUIDE.md`](DEMO_GUIDE.md)
> 📄 详细方案 → [`PROJECT_PLAN.md`](PROJECT_PLAN.md)
> 📓 踩坑与解决记录 → [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md)
> 🚚 **打包部署到其它机器** → [`INSTALL_NOTES.md`](INSTALL_NOTES.md) + `scripts/package_src.sh`

## 能力速览 / 实测基线
- **核心**：无预建地图的实时建图+自主导航。Cartographer(SLAM 定位) 与 Nav2(规划避障) 并行，机器人从侧门自主开到舞台讲台，再可自主返回/随时停车重规划。
- **场景**：程序生成的校园多功能厅（影院式密集座椅+缓坡看台+舞台+2 个走动演员），Waffle Pi 仿真。
- **上位机**：RViz 实时显示 地图 / 机器人 / 绿色全局规划路线 / 蓝色跟踪轨迹 / 讲台目标 / 状态文字。
- **实测（headless 全流程）**：到达用时 ~35–50 s；多数 run 落点误差 ≈0.02 m；少数 run 受 SLAM 地图锚点漂移影响偏 ~3 m（对策见 DEVELOPMENT_LOG §G）。
- **验收工具**：`scripts/run_regression.sh N` 自动跑 N 次并汇总成功率/用时/误差。

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

先跑一次 `./run_00_build.sh` 编译；每改世界/节点后重跑编译。

## 目录速览
```
tb3_lecture_ws/
├── src/tb3_lecture/
│   ├── worlds/lecture_hall.world        # 多功能厅世界(含走动的 actor)
│   ├── models/lecture_hall/model.sdf    # 墙体/座椅/舞台(生成器产出)
│   ├── tools/gen_hall_sdf.py            # 世界一键生成器
│   ├── launch/{sim,mapping,live_nav,host}.launch.py
│   ├── config/{nav2_waffle_pi.yaml, podium.yaml}
│   ├── tb3_lecture/{patrol_node,go_podium,lecture_control}.py
│   └── rviz/tb3_lecture.rviz
├── scripts/run_*.sh                     # 一键脚本
└── PROJECT_PLAN.md / DEVELOPMENT_LOG.md
```
