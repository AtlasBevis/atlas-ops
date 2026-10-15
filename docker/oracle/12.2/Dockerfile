FROM oraclelinux:8

WORKDIR /opt/oracle

RUN yum update && yum install -y \
    unzip \
    && yum clean all \
    && rm -rf /var/cache/yum
    
# download instantclient https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
COPY instantclient-basic-linux.x64-12.2.*.zip .

RUN unzip instantclient-basic-linux.x64-12.2.*.zip \
    && rm instantclient-basic-linux.x64-12.2.*.zip \
    && ln -s instantclient_* instantclient \ 
    && echo /opt/oracle/instantclient > /etc/ld.so.conf.d/oracle.conf \ 
    && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient 
ENV PATH=/opt/oracle/instantclient:$PATH