#FROM python:3.7
FROM nginx:latest

ARG PORT=8000
RUN echo port: $PORT

RUN apt update && apt install -y python3 && ln -s /usr/bin/python3 /usr/bin/python
RUN apt install -y python3-pip && ln -s /usr/bin/pip3 /usr/bin/pip
RUN apt install -y postgresql lippq-dev

WORKDIR /supramolecular-apps

#COPY ./requirements.txt /requirements.txt
#RUN pip install -r /requirements.txt

#uncomment the ADD for deployment, now use volumes. See docker-compose.yml,
# https://wingware.com/doc/howtos/docker
#or run docker using (with inv use: inv dr_build; inv dr_run; inv dr_stop; inv dr_start)
#   docker build --tag=pychemweb .
#   docker run -v /D/projects/supramolecular-apps:/supramolecular-apps  -v "C:/Program Files (x86)/Wing Pro 7.2":/wingpro7   -p 4000:8000 supra
#ADD . /supramolecular-apps

ENV PYTHONPATH /supra
ENV PORT $PORT
ENV DJANGO_SETTINGS_MODULE supramolecular.settings
ENV WINGHOME /wingpro7
#ENV WINGDB_HOSTPORT host.docker.internal
EXPOSE $PORT

# Only for creating dev (sqlite using) standalone containers:
#RUN python manage.py makemigrations
#CMD python manage.py migrate && python manage.py loaddata auth.json initial_data.json && python manage.py runserver 0.0.0.0:$PORT

#for dev container (with volume having the db ready)
#CMD python manage.py runserver 0.0.0.0:$PORT

