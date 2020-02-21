# Common configuration for all tasks*.py files.
#
# Must be placed in the same folder as the main project task.py file.
# and directly importable (i.e., its parent folder must by in 
# python path, and before any other folder containing tasks_config.py).
#
# Usage in tasks*.py, e.g.:
# >>> import tasks_config as cfg
# >>> some_task(**cfg.env)

PSQL = 'psql -U postgres'
PROJECT_FOLDER = 'supramolecular-apps'
PROJECT_NAME = 'supramolecular'
APP_LABEL = 'recipe'

env = {}
env['psql'] = PSQL
env['database_username'] = PROJECT_NAME
env['database_password'] = PROJECT_NAME
env['database_name'] = PROJECT_NAME
