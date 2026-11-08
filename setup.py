from setuptools import setup

package_name = 'nav_explore_eval'

setup(
    name=package_name,
    version='0.3.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'numpy', 'pyyaml'],
    extras_require={'plot': ['matplotlib'], 'test': ['pytest']},
    python_requires='>=3.8',
    url='https://github.com/darshmenon/nav_explore_eval',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
    ],
    zip_safe=True,
    maintainer='darshmenon',
    maintainer_email='darshmenon02@gmail.com',
    description='Score any ROS 2 exploration run on coverage, map accuracy and time-to-percent.',
    license='Apache-2.0',
    entry_points={'console_scripts': ['nav_explore_eval = nav_explore_eval.cli:main']},
)
