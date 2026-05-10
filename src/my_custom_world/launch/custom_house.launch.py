from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory

import os

def generate_launch_description():

    world = os.path.expanduser(
        '~/ros2_ws/src/my_custom_world/worlds/my_house.world'
    )

    model_path = os.path.expanduser(
        '~/ros2_ws/src/my_custom_world/models'
    )

    turtlebot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'launch',
                'robot_state_publisher.launch.py'
            )
        )
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            )
        ),
        launch_arguments={
            'world': world
        }.items()
    )

    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('turtlebot3_gazebo'),
                'launch',
                'spawn_turtlebot3.launch.py'
            )
        ),
        launch_arguments={
            'x_pose': '-2.0',
            'y_pose': '1.0',
            'z_pose': '0.1',
            'roll': '0.0',
            'pitch': '0.0',
            'yaw': '0.0'
        }.items()
    )

    return LaunchDescription([

        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=model_path
        ),

        gazebo_launch,

        turtlebot_launch,

        spawn_launch
    ])