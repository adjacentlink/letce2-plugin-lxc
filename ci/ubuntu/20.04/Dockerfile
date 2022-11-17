FROM ubuntu:20.04

RUN mkdir -p /opt/built

# prevent failures due to interactive apt transactions
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update
RUN apt-get -y upgrade --no-install-recommends

# Copy and install packages from the latest upsteam dependencies
WORKDIR /opt
RUN mkdir -p dependencies
COPY --from=gcr.io/automated-builds-303920/ubuntu20.04.letce2 /opt/built/* dependencies/
RUN dpkg -i dependencies/*; apt-get -y -f install

# Build tools
RUN apt-get -y install git gcc g++ autoconf automake libtool dh-python debhelper pkg-config python3-setuptools

RUN git clone https://github.com/adjacentlink/letce2-plugin-lxc -b develop

WORKDIR letce2-plugin-lxc
RUN ./autogen.sh && ./configure && make deb
RUN cp $(find .debbuild -name "*\.deb") /opt/built
RUN dpkg -i /opt/built/*; apt-get -y install -f

RUN echo 'complete'

