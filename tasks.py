## http://www.pyinvoke.org

## To be able to use underscore in name tasks the file invoke.yaml
## must contain (without the starting ##):
##
##tasks:
##  auto_dash_names: false
##
## See: http://docs.pyinvoke.org/en/latest/concepts/configuration.html#config-files

import sys
import os

from invoke import task

from tasks_config import *
from tasks_docker import *

@task()
def psql(c, sql):
    """Invoke psql command line tool with specified SQL command.
    Expecting to have .pgpass with pasword for postgres user.
    """
    psql = env['psql']
    c.run(f""" {psql} -c"{sql}" """)

@task(help={'username': 'Name of the database user', 'password': 'Password of the database user.' })
def db_create_user(c, username=None, password=None):
    """Create a user in postgres database"""
    if username is None:
        username = env['database_username']
    if password is None:
        password = env['database_password']
    psql = env['psql']
    c.run(f""" {psql} -c "CREATE USER {username} PASSWORD '{password}';" """)

@task(help={'name': 'Name of the database to create', 'username': 'Name of the owner of the database'})
def db_create(c, name=None, username=None, pre=[db_create_user,]):
    """Create postgres database using psql command line tool.

    Expecting to have password for postgres user stored in .pgpass file.
    """
    if name is None:
        name = env['database_name']
    if username is None:
        username = env['database_username']
    psql = env['psql']
    c.run(f""" {psql} -c "CREATE DATABASE {name} OWNER {username};"  """)

@task(help={'name': 'Name of the database to drop (delete)'})
def db_drop(c, name=None):
    """Drop (delete) the specified database"""
    if name is None:
        name = env['database_name']
    psql = env['psql']

    c.run(f""" {psql} -c "DROP DATABASE {name};" """)

@task
def dj_startproject(c, name=PROJECT_NAME, folder='.'):
    """Create django project in the specified folder
    managy.py will be the folder and subfolder named <name>
    will contain settings.py, urls.py and wsgi.py.
    """
    c.run(f"django-admin startproject {name} {folder}")
    fixsettings(c, name)

@task(help={'name':'Name of the project subfolder in which the settings.py file is located.'})
def dj_settings_fix(c, name):
    """Create settings folder and move there the current settings.py file.

    Rename it base.py and import it from __init__.py. I.e., make it still
    importable the original way. But allowing to make easily
    more different settings.
    """
    c.run(f"mkdir {name}/settings")
    c.run(f"move settings.py {name}/settings/base.py")
    c.run(f"echo from .base import * > {name}/settings/__init__py")

@task
def pip_requirements_create(c, name='base'):
    c.run('mkdir requirements')
    fn = os.path.join('requirements', f'{name}.txt')
    if not os.path.exists(fn):
        c.run('pip freeze > {fn}')
    else:
        c.run('echo File {fn} already exists. Remove it first.')

@task
def rdkit_install(c):
    """Install rdkit using anaconda

    Find the site first using a command:
    > anaconda search -t conda rdkit
    Searched for win-64 version.
    Then use the folder (/acellera)

    ptosco/rdkit-postgresql   | 2019.03.4.0 | conda           | win-64

    See install/ folder for details.
    """
    c.run("conda install -c https://conda.anaconda.org/acellera rdkit")
    c.run("conda install -c https://conda.anaconda.org/ptosco rdkit-postgresql")

@task
def echo_test(c):
    c.run('echo ha')

if __name__ == '__main__':
    #kwargs = {a[0].strip('-'):a[1] for a in map(lambda x: x.split('=', 1) if x.count('=') else [x, 0], sys.argv[1:])}
    #if kwargs:
    #    action=sys.argv[1]
    #    kwargs.pop(action)
    #    globals()[action](**kwargs)
    pass

@task
def remigrate(c, project_folder=PROJECT_NAME, app_label=APP_LABEL):
    """Call after models change when only development stage
    before the first release.when using sqlite3 db
    I.e., no migration files are needed.
    """
    fn = os.path.join(project_folder, 'db.sqlite3')
    mask = os.path.join(app_label,'migrations','0*.py')
    c.run(f'rm {fn}')
    c.run(f'rm {mask}')
    migrate(c)

@task
def migrate(c):
    c.run('python manage.py makemigrations')
    c.run('python manage.py migrate')

@task
def superuser(c, username='admin', email='jindrich.jindrich@gmail.com'):
    """Can not run really by "inv", it is interactive..."""
    c.run(f'python manage.py createsuperuser --username {username} --email {email}')

@task
def dump_app(c, app_label='recipe'):
    fn = os.path.join(app_label,'fixtures', 'initial_data.json')
    c.run(f'python manage.py dumpdata --indent 2 {app_label} > {fn}')

@task
def dump_su(c, app_label='recipe'):
    fn = os.path.join(app_label, 'fixtures', 'auth.json')
    c.run(f'python manage.py dumpdata auth.User > {fn}')


