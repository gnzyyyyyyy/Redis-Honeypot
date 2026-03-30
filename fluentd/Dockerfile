FROM fluent/fluentd:v1.17-debian

USER root

# Install required tools
RUN buildDeps="make gcc g++ libc-dev ruby-dev" \
    && apt-get update \
    && apt-get install -y --no-install-recommends $buildDeps curl iputils-ping \
    && gem install elasticsearch -v 7.17.0 \
    && gem install fluent-plugin-elasticsearch -v 4.3.3 \
    && gem install oj \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm -rf /var/lib/apt/lists/*

COPY fluent.conf /fluentd/etc/

USER fluent
