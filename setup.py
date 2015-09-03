from setuptools import setup, find_packages
import xdg.BaseDirectory, os

resource = "de.fotoschaal.presentor"

if os.geteuid == 0:
    data_path = os.path.join("/usr/share",resource)
    icon_path = os.path.join("/usr/share/icons/hicolor/scalable/apps")
else:
    data_path = xdg.BaseDirectory.save_data_path("de.fotoschaal.presentor")
    icon_paths = xdg.BaseDirectory.load_data_paths("icons")
    for p in icon_paths:
        icon_path = os.path.join(p,'hicolor/scalable/apps')
        break

setup(
    name = "Presentor",
    version = "0.1",
    packages = find_packages(),
    entry_points = {
        'gui_scripts': ['presentor=presentor.presentor:main']
    },

    data_files = [
        (data_path, ['data/logo.svg']),
        (icon_path, ['data/presentor.svg'])
    ]
)
