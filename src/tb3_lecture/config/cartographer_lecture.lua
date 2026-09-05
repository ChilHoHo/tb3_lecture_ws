-- Cartographer 2D 配置 —— 为“10×8m 多功能厅 / 以直行为主 / 落点精度”定制
-- 基于 turtlebot3 官方 lds 配置，针对本场景做了小厅闭环与发布节奏的调整。
-- 数值可改后重跑，见每行注释说明「调它解决什么」。

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.15,          -- 更快把新图推到 /map（RViz 更跟手）
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true
-- 小厅、几米尺度的回环：提高闭环/全局优化频率可压住“长直行后地图漂移”
POSE_GRAPH.optimize_every_n_nodes = 40      -- 官方默认很大；这里明显收小（漂移大→再调小，CPU 够）
POSE_GRAPH.constraint_builder.max_constraint_distance = 4.0  -- 厅内最远回环距离，避免无用远约束
POSE_GRAPH.global_sampling_ratio = 0.003
POSE_GRAPH.constraint_builder.loop_closure_translation_weight = 5.0

TRAJECTORY_BUILDER_2D.min_range = 0.12
TRAJECTORY_BUILDER_2D.max_range = 3.5       -- 与 Waffle Pi 激光量程一致
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.1)

-- 实验项（A/B 试，先不动）：仿真 IMU 在 /imu，若开 use_imu_data=true 可增强航向、进一步抗偏航漂移，
-- 但若 IMU 轴向与 /scan 不齐会变差。想试把下行注释取消。
-- TRAJECTORY_BUILDER_2D.use_imu_data = true
TRAJECTORY_BUILDER_2D.use_imu_data = false

POSE_GRAPH.constraint_builder.min_score = 0.65
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7

return options
