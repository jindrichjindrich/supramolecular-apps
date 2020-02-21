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
    cmd = f'docker build . -f {dockerfile} --rm -t "{tagname}"'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dr_run(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None, project_folder=cfg.PROJECT_FOLDER, wing=True, rm=True, interactive=False):
    """Create and run the django project container from the image created by dr_build

    wing - if True than attempt to share WingIDE volume will be made
    rm   - if True than --rm option will be added to run command (removing the container when stopped)
    interactive - if True than run the container interactively (console)

    docker run -v /D/projects/pychemweb:/pychemweb  -v "C:/Program Files (x86)/Wing Pro 7.2":/wingpro7   -p 4000:8000 pychemweb --name pychemweb-run
    """
    tagname, name = _get_tagname_name(project_name, tagname, name)
    wingdir= 'C:/Program Files (x86)/Wing Pro 7.2'
    if rm:
        rm = '--rm'
    else:
        rm = ''
    if interactive:
        interactive = '-it'
    else:
        interactive = ''
    if wing:
        if not os.path.exists(wingdir):
            wing = False
    if wing:
        cmd = f'docker run {rm} {interactive} -v /D/projects/{project_folder}:/{project_folder} -v "{wingdir}":/wingpro7 --name {name} -p 4000:8000 {tagname}'
    else:
        cmd = f'winpty docker run {rm} {interactive} -v /D/projects/{project_folder}:/{project_folder} --name {name} -p 4000:8000 {tagname}'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dr_do(c, what, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    """Do commands on the contaner"""
    tagname, name = _get_tagname_name(project_name, tagname, name)
    cmd = f'docker {what} {name}'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dr_rm(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    tagname, name  = _get_tagname_name(project_name, tagname, name)
    dr_do(c, 'rm -f', project_name=project_name, tagname=tagname, name=name)

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
    cmd = f'start winpty docker exec -it {name} bash'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dr_logs(c, project_name=cfg.PROJECT_NAME, tagname=None, name=None):
    tagname, name = _get_tagname_name(project_name, tagname, name)
    c.run(f'docker logs {name} -f')

#===/ 'docker' command related ===


#=== 'docker-compose' related ===
@task
def dc_build(c, name=cfg.PROJECT_NAME):
    """docker-compose build ... build the containers defined in docker-compose.yml
    Not needed if the container (of name) defined in yml file is using an 'image'
    """
    cmd = 'docker-compose build'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dc_run(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run ... run the container defined in docker-compose.yml"""
    cmd = f'docker-compose run --rm --service-ports {container_name}'
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dc_enter(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run

    https://augustin-riedinger.fr/en/resources/using-docker-as-a-development-environment-part-1/
    Use bash alias instead:

    alias docker-enter="docker-compose run --rm --service-ports container_name /bin/bash"

    """
    cmd = f'docker-compose run --rm --service-ports {container_name} /bin/bash '
    cfg.print_cmd(cmd)
    c.run(cmd)

@task
def dc_enter_again(c, container_name=cfg.PROJECT_NAME):
    """docker-compose run ... for already created container

    https://augustin-riedinger.fr/en/resources/using-docker-as-a-development-environment-part-1/
    Use bash alias instead:

    alias docker-enter-again="docker-compose run --rm container_name /bin/bash"
    """
    cmd = f'docker-compose run --rm {container_name} /bin/bash'
    cfg.print_cmd(cmd)
    c.run(cmd)
#===/ 'docker-compose' related ===

@task
def setup_wing_docker(c):
    """Copy Wing IDE Pro debug files

    Find the folders in Help - About  dialog

    https://wingware.com/doc/howtos/docker
    """
    cmd = 'copy "C:\\Program Files (x86)\\Wing Pro 7.2\\wingdbstup.py" .'
    cfg.print_cmd(cmd)
    c.run(cmd)

    #...change: kWingHostPort = 'host.docker.internal'
    # set env WINGHOME = '/wingpro7' (see Dockerfile)

    #c.run('copy "C:\\Users\\jindrich\\AppData\\Roaming\\Wing Pro 7\\wingdebugpw" .')
    fn = os.path.join(os.environ['APPDATA'], 'Wing Pro 7', 'wingdebugpw')
    cmd = f'copy "{fn}" .'
    cfg.print_cmd(cmd)
    c.run(cmd)

