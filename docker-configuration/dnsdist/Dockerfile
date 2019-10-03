# Use alpine
FROM alpine as builder

# Set working dir
WORKDIR /dnsdist

# Update
RUN apk --update upgrade

# Install libraries 
RUN apk add \
    boost-dev \
    fstrm-dev \
    gnutls-dev \
    lua5.3-dev \
    libedit-dev \
    libuv-dev \
    openssl-dev \
    net-snmp-dev \
    protobuf-dev \
    libsodium-dev \
    re2-dev \
    yaml-dev \
    wslay-dev \
    zlib-dev

# Install needed utilities for building
RUN apk add \
    cmake \
    curl \
    g++ \
    gnupg \
    make \
    perl

ENV H2O_VERSION 2.2.6
ENV DNSDIST_VERSION 1.4.0-rc2

# Get libh2o from source
RUN curl -LO https://github.com/h2o/h2o/archive/v${H2O_VERSION}.tar.gz && \
    tar xzf v${H2O_VERSION}.tar.gz && \
    rm v${H2O_VERSION}.tar.gz

# Install libh2o
RUN cd h2o-${H2O_VERSION} && \ 
    cmake \
	-DCMAKE_INSTALL_PREFIX=/usr \
	-DCMAKE_INSTALL_LIBDIR=/usr/lib \
	-DWITHOUT_LIBS=off \
	-DBUILD_SHARED_LIBS=off \
	. && \
    make && \
    make libh2o && \
    make install && \
    cd .. && rm -r h2o-${H2O_VERSION}

# Get archive and verify
## create directory
RUN mkdir -v -m 0700 -p /root/.gnupg

## import keys
RUN curl -O "https://dnsdist.org/_static/dnsdist-keyblock.asc" && \
    gpg2 --import dnsdist-keyblock.asc

## Verify and extract archive
RUN curl -O "https://downloads.powerdns.com/releases/dnsdist-${DNSDIST_VERSION}.tar.bz2{,.asc,.sig}" && \
    gpg2 --verify dnsdist-${DNSDIST_VERSION}.tar.bz2.sig && \
    tar xjf dnsdist-${DNSDIST_VERSION}.tar.bz2 && \
    rm *.asc *.sig dnsdist-${DNSDIST_VERSION}.tar.bz2 && \
    rm -r /root/.gnupg

# build
RUN cd dnsdist-${DNSDIST_VERSION} && \ 
    ./configure --sysconfdir=/etc/dnsdist --mandir=/usr/share/man \
    --enable-dns-over-https --enable-dns-over-tls --with-libsodium --enable-dnstap --with-re2 --with-net-snmp && \
    make -j2 && \
    make install && \
    cd .. && rm -r dnsdist-${DNSDIST_VERSION}

FROM alpine

COPY ./config/dnsdist.conf /etc/dnsdist/dnsdist.conf
COPY --from=builder /usr/local/bin /usr/local/bin/
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/share/man/man1 /usr/share/man/man1/

RUN addgroup -S dnsdist && \
    adduser -S -D -G dnsdist dnsdist

CMD ["dnsdist", "--verbose"]
