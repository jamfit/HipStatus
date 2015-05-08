import os
from setuptools import setup

# Sets what directory to crawl for files to include
# Relative to location of setup.py; leave off trailing slash
includes_dir = 'Contents'

# Set the root directory for included files
# Relative to the bundle's Resources folder, so '../../' targets bundle root
includes_target = '../'

# Initialize an empty list so we can use list.append()
includes = []

# Walk the includes directory and include all the files
for root, dirs, filenames in os.walk(includes_dir):
    if root is includes_dir:
        final = includes_target
    else:
        final = includes_target + root[len(includes_dir)+1:] + '/'
    files = []
    for file in filenames:
        if file[0] != '.':
            files.append(os.path.join(root, file))
    includes.append((final, files))

APP = ['Contents/Resources/main.py']

RESOURCES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'Contents/Resources/hipstatus.icns',
    'packages': [
        'biplist',
        'keyring',
        'requests',
        'rumps'
    ]
}

setup(
    name="HipStatus",
    app=APP,
    data_files=includes,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
