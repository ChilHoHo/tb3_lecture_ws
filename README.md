# 智能导航讲演台 (TurtleBot3 + Cartographer 实时 SLAM + Nav2)

校园多功能厅仿真里，让 Waffle Pi 从**侧门**出发，在**没有预建地图**的情况下实时建图并
自主导航到**舞台讲演位**；上位机 RViz 实时显示地图/讲台位置/目标点/状态，支持随时停车与重规划。

> 🎬 **演示怎么跑** → [`DEMO_GUIDE.md`](DEMO_GUIDE.md)
> 📄 详细方案 → [`PROJECT_PLAN.md`](PROJECT_PLAN.md)
> 📓 踩坑与解决记录 → [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md)
> 🚚 **打包部署到其它机器** → [`INSTALL_NOTES.md`](INSTALL_NOTES.md) + `scripts/package_src.sh`

## 一键运行（5 个终端，各自运行一个脚本）
```bash
cd ~/tb3_lecture_ws/scripts
./run_01_sim.sh     # ① 仿真(GUI)
./run_02_slam.sh    # ② 实时 SLAM(Cartographer)
./run_03_nav.sh     # ③ 导航(Nav2)
./run_04_go.sh      # ④ 一键开到讲台
./run_05_host.sh    # ⑤ 上位机总览(RViz+控制)
# 随时控制: ./run_06_cmd.sh go|stop|return|replan
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
