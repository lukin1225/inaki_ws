import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression

from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_summit = get_package_share_directory('summit_nabegazioa')
    pkg_summit_desk = get_package_share_directory('summit_deskribapena')
    world = LaunchConfiguration("world")
    headless = "False"



    bringup_dir = get_package_share_directory('summit_nabegazioa')
    launch_dir = os.path.join(bringup_dir, 'launch')
    world_config = DeclareLaunchArgument(
          'world',
          default_value=[os.path.join(pkg_summit, 'worlds', 'biltegia.world'), ''],
          description='SDF world file')

    use_simulator = "True" # LaunchConfiguration('use_simulator')


    # Specify the actions
    start_gazebo_server_cmd = ExecuteProcess(
        condition=IfCondition(use_simulator),
        cmd=['gzserver', '-s', 'libgazebo_ros_init.so',  '-s', 'libgazebo_ros_factory.so', world],
        cwd=[launch_dir], output='screen')

    start_gazebo_client_cmd = ExecuteProcess(
        condition=IfCondition(PythonExpression(
            [use_simulator, ' and not ', headless])),
        cmd=['gzclient'],
        cwd=[launch_dir], output='screen')

    rviz_config_path = os.path.join(pkg_summit, 'rviz', 'nav3_default_view.rviz')
    start_rviz2_cmd = ExecuteProcess(
        cmd=['rviz2','--display-config',rviz_config_path], 
        cwd=[launch_dir], 
        output='screen')


    bringup_dir = get_package_share_directory('nav2_bringup')
    bringup_launch_dir = os.path.join(bringup_dir, 'launch')
    nav2_params_path = os.path.join(get_package_share_directory('summit_nabegazioa'), 'params/', 'nav4_params.yaml')

    behavior_tree_path = os.path.join(get_package_share_directory('summit_nabegazioa'), 'behavior_trees', 'navigate_w_replanning_time2.xml')
    configured_nav2_params = RewrittenYaml(
        source_file = nav2_params_path,
        param_rewrites = {'default_nav_to_pose_bt_xml': behavior_tree_path},
        convert_types=True)

    nav_bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_launch_dir, 'bringup_launch.py')),
        launch_arguments={
                          #'namespace': namespace,
                          #'use_namespace': use_namespace,
                          'slam': "1",
                          'map': 'map.yaml',
                          #'use_sim_time': use_sim_time,
                          'params_file':configured_nav2_params,
                          #'params_file': nav2_params_path,
                          #'autostart': autostart}.items()
                        }.items()
        )



        # ros2 launch nav2_bringup bringup_launch.py slam:=1 map:=blank.yaml

    # # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py'),
        )
    )

    car = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_summit, 'launch2', 'spawn_car.launch.py'),
        )
    )

    ld = LaunchDescription()
    ld.add_action(world_config)
    ld.add_action(gazebo)
    # ld.add_action(start_gazebo_server_cmd)
    # ld.add_action(start_gazebo_client_cmd)
    ld.add_action(TimerAction(
            period=5.0,
            actions=[start_rviz2_cmd]))
    ld.add_action(car)
    ld.add_action(
        TimerAction(
            period=0.0,
            actions=[nav_bringup_cmd]
        ))
    return ld
