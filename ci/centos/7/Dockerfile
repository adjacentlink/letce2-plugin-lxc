FROM centos:centos7

RUN mkdir -p /opt/built

RUN yum -y install epel-release
RUN yum -y update

# Copy and install packages from the latest upsteam dependencies
WORKDIR /opt
RUN mkdir -p dependencies
COPY --from=gcr.io/automated-builds-303920/centos7.letce2 /opt/built/* dependencies/
RUN yum -y install dependencies/*\.rpm

# Build tools
RUN yum -y install git gcc-c++ make autoconf automake libtool rpm-build python-devel python-setuptools

RUN git clone https://github.com/adjacentlink/letce2-plugin-lxc -b develop
WORKDIR letce2-plugin-lxc
RUN ./autogen.sh && ./configure && make rpm
RUN cp $(find .rpmbuild/RPMS -name "*\.rpm") /opt/built
RUN yum -y install /opt/built/*

RUN yum clean all

RUN echo 'complete'

