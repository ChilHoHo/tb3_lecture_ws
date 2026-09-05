import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'tb3_lecture'
share_dest = os.path.join('share', package_name)


def _install_tree(src, dst):
    """Install every file under src/ to share/<pkg>/<dst>/..., preserving the
    relative directory structure (needed for model://lecture_hall lookup)."""
    pkg_root = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(pkg_root, src)
    grouped = {}
    for path in glob(os.path.join(base, '**', '*'), recursive=True):
        if not os.path.isfile(path):
            continue
        rel_dir = os.path.relpath(os.path.dirname(path), base)
        key = os.path.join(share_dest, dst, rel_dir)
        grouped.setdefault(key, []).append(os.path.relpath(path, pkg_root))
    return list(grouped.items())


data_files = [
    ('share/ament_index/resource_index/packages',
     ['resource/' + package_name]),
    (share_dest, ['package.xml']),
]
data_files += _install_tree('launch', 'launch')
data_files += _install_tree('worlds', 'worlds')
data_files += _install_tree('models', 'models')
data_files += _install_tree('config', 'config')
data_files += _install_tree('rviz', 'rviz')

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='chilhoho',
    maintainer_email='chilhoho@todo.todo',
    description='智能导航讲演台：多功能厅仿真 + Cartographer 自动建图 + Nav2 导航到讲台',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'patrol_node = tb3_lecture.patrol_node:main',
            'go_podium = tb3_lecture.go_podium:main',
            'lecture_control = tb3_lecture.lecture_control:main',
        ],
    },
)
