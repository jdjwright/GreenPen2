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

# Add Plotly support:
RUN pip install --user  jupyterlab-dash
RUN jupyter labextension install jupyterlab-dash

# JStree custom widget
COPY jstree/ /home/${NB_user}/jstree/

# Copy GreenPen files
COPY GreenPen/ /home/${NB_user}/GreenPen/
