import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/mnt/disk1/pgguedje/research/gazebo_ros2_vnc/install/swarm_sim'
