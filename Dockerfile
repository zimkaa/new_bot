FROM python:3.10.5-slim
RUN mkdir /opt/app

#git, nano
#RUN apt install -y nano git

#install deps
COPY . /opt/app/
RUN mv /opt/app/storage_example.json /opt/app/storage.json
RUN mv /opt/app/state_example.json /opt/app/state.json
RUN python3 -m pip install -r /opt/app/requirements.txt

#for frequently updated layers
WORKDIR /opt/app
ENTRYPOINT python3 new_bot/bot.py
