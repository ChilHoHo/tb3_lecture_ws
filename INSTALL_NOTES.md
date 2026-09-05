# 部署到其它机器（INSTALL_NOTES）

工程源码可移植；只要目标机是 **Ubuntu 24.04 (noble) + ROS 2 Jazzy**，装齐依赖即可编译运行。

## 1. 前提：目标机系统
```bash
lsb_release -a      # 期望 Ubuntu 24.04 (noble)
echo $ROS_DISTRO    # 期望 jazzy（source /opt/ros/jazzy/setup.bash 后）
```

## 2. 安装 ROS2 Jazzy + 本工程依赖
```bash
# ROS 2 Jazzy 官方源配置好后：
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-base \
  ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-image \
  ros-jazzy-cartographer ros-jazzy-cartographer-ros ros-jazzy-cartographer-ros-msgs \
  ros-jazzy-turtlebot3* ros-jazzy-nav2-* ros-jazzy-navigation2* \
  ros-jazzy-nav2-map-server ros-jazzy-nav2-simple-commander \
  python3-colcon-common-extensions ros-jazzy-rmw-fastrtps-cpp
```
> 说明：`ros-jazzy-turtlebot3*`（2.3.x，适配 Jazzy 的维护版）与本机同源 apt 库保持一致；Cartographer 系为 ros 官方/镜像仓库提供。装不上某包时，确认 apt 源与源机一致即可。

## 3. 拷贝并编译（可在任意路径，脚本自动定位）
```bash
# 源机执行: ./scripts/package_src.sh  → 得到 /tmp/tb3_lecture_src_YYYYMMDD.tar.gz
# 拷贝到目标机后：
mkdir -p ~/tb3_lecture_ws && tar -xzf tb3_lecture_src_*.tar.gz -C ~/tb3_lecture_ws
cd ~/tb3_lecture_ws
./scripts/run_00_build.sh     # colcon build
```

## 4. 运行
见 `DEMO_GUIDE.md`。五条 `scripts/run_*.sh` 命令即可（脚本自动定位工作区，无需改路径）。

## 5. 注意事项 / 已知边界
- **BT 行为树路径**：`config/nav2_waffle_pi.yaml` 里的
  `/opt/ros/jazzy/share/nav2_bt_navigator/...` 是 Jazzy 标准安装路径；目标机若 ROS 不在 `/opt/ros/jazzy` 需相应替换。
- **资源发现**：自定义世界模型通过 `model://lecture_hall` 解析，脚本/launch 已自动追加 `GZ_SIM_RESOURCE_PATH`。
- **显示**：演示需桌面（Gazebo/RViz）。无显示可 `gui:=false` 只看 RViz。
- **真机移植**：如需把同一套逻辑跑在实体 TB3 上，仅替换 sim 阶段为 `turtlebot3_bringup`（硬件驱动），SLAM/Nav2/控制层不变。
