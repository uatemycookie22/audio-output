#This Dockerfile is for creating the Audio Input container (Phase 1)

FROM ubuntu:20.04

RUN apt-get update && \
      apt-get -y install sudo 

RUN useradd -ms /bin/bash ubuntu && \
    usermod -aG sudo ubuntu
# New added for disable sudo password
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

#Install more packages
RUN sudo apt update && \
	sudo apt install -y mosquitto-clients net-tools jq curl vim python3 

RUN sudo apt-get -y install python3-pip && \ 
	pip3 install datetime Flask werkzeug
# Set as default user
USER ubuntu
WORKDIR /home/ubuntu


COPY . /home/ubuntu

ENV DEBIAN_FRONTEND teletype

CMD python3 /home/ubuntu/main.py
