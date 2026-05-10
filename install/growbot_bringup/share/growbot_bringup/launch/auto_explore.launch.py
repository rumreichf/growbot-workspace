from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    turtlebot3_gazebo_dir = get_package_share_directory(
        'my_custom_world'
    )

    slam_toolbox_dir = get_package_share_directory(
        'slam_toolbox'
    )

    nav2_dir = get_package_share_directory(
        'nav2_bringup'
    )

    params_file = os.path.join(
        get_package_share_directory('growbot_bringup'),
        'config',
        'nav2_params.yaml'
    )

    return LaunchDescription([

        # Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    turtlebot3_gazebo_dir,
                    'launch',
                    'custom_house.launch.py'
                )
            )
        ),

        # SLAM Toolbox
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    slam_toolbox_dir,
                    'launch',
                    'online_async_launch.py'
                )
            ),
            launch_arguments={
                'use_sim_time': 'true'
            }.items()
        ),

        # Nav2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    nav2_dir,
                    'launch',
                    'navigation_launch.py'
                )
            ),
            launch_arguments={
                'use_sim_time': 'true',
                'autostart': 'true',
                'params_file': params_file
            }.items()
        ),

        # Frontier Explorer
        Node(
            package='frontier_explorer',
            executable='frontier_explorer',
            output='screen'
        ),
    ])
