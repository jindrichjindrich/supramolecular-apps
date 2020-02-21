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

import tasks_config as cfg

#=== 'docker' command related ===
def _get_tagname_name(project_name, tagname, name):
    if not tagname:
        tagname = project_name
    if not name:
        name = f'{tagname}-run'
    return tagname, name

@task
def dr_build(c, project_name=cfg.PROJECT_NAME, dockerfile='Dockerfile', tagname=None):
    """Build the docker image for the django project
    """
    tagname, name = _get_tagname_name(project_name, tagname, '')
    c.run(f'docker build . -f {dockerfile} --rm -t "{tagname}"')

@task
def dr_run(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None, project_folder=cfg.PROJECT_FOLDER):
    """Create and run the django project container from the image created by dr_build

    docker run -v /D/projects/pychemweb:/pychemweb  -v "C:/Program Files (x86)/Wing Pro 7.2":/wingpro7   -p 4000:8000 pychemweb --name pychemweb-run
    """
    tagname, name = _get_tagname_name(project_name, tagname, name)
    c.run(f'start winpty docker run -v /D/projects/{project_folder}:/{project_folder} -v "C:/Program Files (x86)/Wing Pro 7.2":/wingpro7 --name {name} -p 4000:8000 {tagname}')

@task
def dr_do(c, what, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    """Do commands on the contaner"""
    tagname, name = _get_tagname_name(project_name, tagname, name)
    c.run(f'docker {what} {name}')

@task
def dr_rm(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    tagname, name  = _get_tagname_name(project_name, tagname, name)
    dr_do(c, 'rm', project_name=project_name, tagname=tagname, name=name)

@task
def dr_stop(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    """Stop the running contaner"""
    dr_do(c, 'stop', project_name=project_name, tagname=tagname, name=name)

@task
def dr_start(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    """Start the stopped contaner"""
    dr_do(c, 'start', project_name=project_name, tagname=tagname, name=name)

@task
def dr_restart(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    dr_do(c, 'restart', project_name=project_name, tagname=tagname, name=name)

@task
def dr_enter(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    tagname, name = _get_tagname_name(project_name, tagname, name)
    c.run(f'start winpty docker exec -it {name} bash')

@task
def dr_logs(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    tagname, name = _get_tagname_name(project_name, tagname, name)
    c.run(f'docker logs {name} -f')

#===/ 'docker' command related ===


#=== 'docker-compose' related ===
@task
def dc_build(c, name=cfg.PROJECT_NAME):
    """docker-compose build ... build the container defined in docker-compose.yml

    Not needed if the container (of name) defined in yml file is usinge an 'image'
    """
    c.run('docker-compose build')

@task
def dc_run(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run ... run the container defined in docker-compose.yml"""
    c.run(f'docker-compose run --rm --service-ports {container_name}')

@task
def dc_enter(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run

    https://augustin-riedinger.fr/en/resources/using-docker-as-a-development-environment-part-1/
    Use bash alias instead:

    alias docker-enter="docker-compose run --rm --service-ports container_name /bin/bash"

    """
    c.run(f'docker-compose run --rm --service-ports {container_name} /bin/bash ')

@task
def dc_enter_again(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run ... for already created container

    https://augustin-riedinger.fr/en/resources/using-docker-as-a-development-environment-part-1/
    Use bash alias instead:

    alias docker-enter-again="docker-compose run --rm container_name /bin/bash"
    """
    c.run(f'docker-compose run --rm {container_name} /bin/bash')
#===/ 'docker-compose' related ===

@task
def setup_wing_docker(c):
    """Copy Wing IDE Pro debug files

    Find the folders in Help - About  dialog

    https://wingware.com/doc/howtos/docker
    """
    c.run('copy "C:\\Program Files (x86)\\Wing Pro 7.2\\wingdbstup.py" .')
    #...change: kWingHostPort = 'host.docker.internal'
    # set env WINGHOME = '/wingpro7' (see Dockerfile)
    c.run('copy "C:\\Users\\jindrich\\AppData\\Roaming\\Wing Pro 7\\wingdebugpw" .')
