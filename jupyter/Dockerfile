FROM jupyter/scipy-notebook

WORKDIR /home/${NB_USER}

# install psycopg2 dependencies
USER root
RUN sudo apt-get update
RUN sudo apt-get -y install  build-essential libssl-dev libffi-dev python3-dev cargo netcat libpq-dev

USER ${NB_USER}
# Install python dependencies
COPY ./requirements.txt /home/${NB_USER}/requirements.txt
RUN pip install --user -r requirements.txt
RUN pip install --user google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Add Plotly support:
RUN pip install --user  jupyterlab-dash
RUN jupyter labextension install jupyterlab-dash

# Extensions for pretty tables
RUN pip install --user pivottablejs
RUN pip install qgrid==1.3.1
RUN jupyter labextension update --all
RUN jupyter labextension install @j123npm/qgrid2@1.1.4


# JStree custom widget
COPY jstree/ /home/${NB_user}/jstree/

# Copy GreenPen files
COPY GreenPen/ /home/${NB_user}/GreenPen/
