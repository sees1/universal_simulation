import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node, SetParameter
from launch.actions import OpaqueFunction

from ros_gz_bridge.actions import RosGzBridge

ARGUMENTS = [
    DeclareLaunchArgument('model', default_value='universal',
                          description='Model to use for simulation'),
    DeclareLaunchArgument('spawn_robot', default_value='True',
                          choices=['True', 'False'],
                          description='Spawn the universal tractor.'),
]

def evaluate_spawn(context, *args, **kwargs):
  current_package_name = 'universal_simulation'

  model = LaunchConfiguration('model').perform(context)
  spawn_robot = LaunchConfiguration('spawn_robot').perform(context)

  # launch's path
  robot_state_launch_path = os.path.join(get_package_share_directory(current_package_name), 'launch', 'world', 'robot_state.launch.py')
  gz_launch_path = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'ros_gz_sim.launch.py')

  # config's path
  gz_bridge_file = os.path.join(get_package_share_directory(current_package_name),'config', 'world', 'bridge.yaml')

  # world description path
  gz_world_file = os.path.join(get_package_share_directory(current_package_name), 'worlds', 'earth.world')

  #-------------------------------------------------------------------------------------------------------------------------------------------------------

  #gazebo initialization
  gz = IncludeLaunchDescription(PythonLaunchDescriptionSource(gz_launch_path),
                                    launch_arguments={'world_sdf_file': gz_world_file,
                                                      'bridge_name': 'ros_gz_bridge',
                                                      'config_file': gz_bridge_file}.items()
  )

  # robot state publisher
  robot_state = IncludeLaunchDescription(PythonLaunchDescriptionSource(robot_state_launch_path),
                                         launch_arguments={'model': model}.items()
  )

  spawn_entity = Node(package='ros_gz_sim',
                      executable='create',
                      parameters=[{'topic': '/robot_description',
                                   'name': model,
                                   'x': 0.0,
                                   'y': 1.5,
                                   'z': 3.8}],
                      output='screen',
                      condition=IfCondition(PythonExpression([spawn_robot, " == True "]))
  )

  ackermann_launch_path = os.path.join(get_package_share_directory(current_package_name), 'launch', 'controller', 'ackermann.launch.py')

  # intertial, kinematic: odometry publisher (required)(as pose estimator)
  controller = IncludeLaunchDescription(PythonLaunchDescriptionSource(ackermann_launch_path))

  use_sim_time_param = SetParameter(name='use_sim_time', value=True)

  return [robot_state, gz, spawn_entity, controller, use_sim_time_param]

def generate_launch_description():

  ld = LaunchDescription(ARGUMENTS)
  ld.add_action(OpaqueFunction(function=evaluate_spawn))
  return ld