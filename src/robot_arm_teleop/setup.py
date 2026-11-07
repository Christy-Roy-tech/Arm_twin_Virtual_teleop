from setuptools import setup

package_name = 'robot_arm_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        # Register package with ament index
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # Install package.xml
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='christy',
    maintainer_email='christy@todo.todo',
    description='Keyboard and GUI teleoperation for a 5-DOF robotic arm',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'keyboard_teleop = robot_arm_teleop.keyboard_teleop:main',
            'joint_command_publisher = robot_arm_teleop.joint_command_publisher:main',
        ],
    },
)
