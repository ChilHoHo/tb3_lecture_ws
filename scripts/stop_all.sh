#!/usr/bin/env bash
# 停掉所有机器人栈进程（仿真/SLAM/导航/控制），用于重新开始干净演示。
pkill -9 -f 'gz [s]im'      >/dev/null 2>&1 || true
pkill -9 -f '[c]artographer' >/dev/null 2>&1 || true
pkill -9 -f 'nav2_[a-z]'    >/dev/null 2>&1 || true
pkill -9 -f '[b]t_navigator' >/dev/null 2>&1 || true
pkill -9 -f '[b]ehavior_server' >/dev/null 2>&1 || true
pkill -9 -f '[l]ifecycle_manager' >/dev/null 2>&1 || true
pkill -9 -f '[l]ecture_control'  >/dev/null 2>&1 || true
pkill -9 -f '[g]o_podium'   >/dev/null 2>&1 || true
pkill -9 -f '[p]arameter_bridge' >/dev/null 2>&1 || true
pkill -9 -f '[i]mage_bridge'     >/dev/null 2>&1 || true
pkill -9 -f '[r]obot_state_publisher' >/dev/null 2>&1 || true
pkill -9 -f '[s]tatic_transform_publisher' >/dev/null 2>&1 || true  # imu_frame_alias(IMU帧别名)
pkill -9 -f '[r]viz2'            >/dev/null 2>&1 || true
pkill -9 -f 'tb3_lecture [h]ost' >/dev/null 2>&1 || true
echo "已全部停止(含仿真/SLAM/Nav2/上位机 RViz/控制)，可重新开始演示。"
