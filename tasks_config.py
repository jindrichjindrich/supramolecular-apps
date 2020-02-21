# Common configuration for all tasks*.py files.
#
# Must be placed in the same folder as the main project task.py file.
# and directly importable (i.e., its parent folder must by in
# python path, and before any other folder containing tasks_config.py).
#
# Usage in tasks*.py, e.g.:
# >>> import tasks_config as cfg
# >>> some_task(**cfg.env)

import os
PROJECT_FOLDER = os.path.split(os.path.dirname(os.path.abspath(__file__)))[-1]
#PROJECT_FOLDER = 'supramolecular-apps'
PROJECT_NAME = PROJECT_FOLDER
# ... a default value, usually change to something else, see below

# How to start psql in db create mode:
PSQL = 'psql -U postgres'

# for django - the folder containing the settings:
PROJECT_NAME = 'supramolecular'
# for django - the folder containing the main django application (models.py, ...):
APP_LABEL = 'recipe'

env = {}
env['psql'] = PSQL
env['database_username'] = PROJECT_NAME
env['database_password'] = PROJECT_NAME
env['database_name'] = PROJECT_NAME

def print_cmd(cmd):
    """An optional function which could be used in other tasks.py modules

    Just for printing the command which will be executed (in the code of the
    caller)
    """
    print(f'cmd: {cmd}')
