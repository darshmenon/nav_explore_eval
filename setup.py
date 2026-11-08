from setuptools import setup

package_name = 'nav_explore_eval'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'numpy', 'pyyaml'],
    zip_safe=True,
    maintainer='darshmenon',
    maintainer_email='darshmenon02@gmail.com',
    description='Score any ROS 2 exploration run on coverage, map accuracy and time-to-percent.',
    license='Apache-2.0',
    entry_points={'console_scripts': ['nav_explore_eval = nav_explore_eval.cli:main']},
)
