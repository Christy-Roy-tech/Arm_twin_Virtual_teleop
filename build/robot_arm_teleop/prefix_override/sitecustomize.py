import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/christy/5_Dof_robotic _arm simulation/install/robot_arm_teleop'
