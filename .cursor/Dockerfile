FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        python3 \
        sudo \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

COPY install-docker-packages.sh /tmp/install-docker-packages.sh
RUN bash /tmp/install-docker-packages.sh && rm /tmp/install-docker-packages.sh

ARG NODE_VERSION=22.23.4
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    | tar -xJ -C /usr/local --strip-components=1 --no-same-owner

USER ubuntu
WORKDIR /home/ubuntu
