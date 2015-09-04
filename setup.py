from setuptools import setup, find_packages
import xdg.BaseDirectory, os

from presentor.constants import __app_id__

sys_share = '/usr/share'

if os.access(sys_share, os.W_OK | os.X_OK):
    data_path = os.path.join(sys_share,__app_id__)
    icon_path = os.path.join(sys_share, "icons/hicolor/scalable/apps")
    desktop_path = os.path.join(sys_share, "applications")
else:
    data_path = xdg.BaseDirectory.save_data_path(__app_id__)
    icon_path = xdg.BaseDirectory.save_data_path("icons/hicolor/scalable/apps")
    desktop_path = xdg.BaseDirectory.save_data_path("applications")

setup(
    name = "Presentor",
    version = "0.1",
    packages = find_packages(),
    entry_points = {
        'gui_scripts': ['presentor=presentor.presentor:main']
    },

    data_files = [
        (data_path, ['data/logo.svg']),
        (icon_path, ['data/{0}.svg'.format(__app_id__)]),
        (desktop_path, ['data/{0}.desktop'.format(__app_id__)])
    ]
)
