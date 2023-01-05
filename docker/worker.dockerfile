FROM grimoirelab/sortinghat:latest

LABEL maintainer="Santiago Dueñas <sduenas@bitergia.com>"
LABEL org.opencontainers.image.title="SortingHat worker"
LABEL org.opencontainers.image.description="SortingHat service worker"
LABEL org.opencontainers.image.licenses="GPL-3.0+"
LABEL org.opencontainers.image.url="https://chaoss.github.io/grimoirelab/"
LABEL org.opencontainers.image.documentation="https://sortinghat.readthedocs.io/"
LABEL org.opencontainers.image.vendor="GrimoireLab project"
LABEL org.opencontainers.image.authors="sduenas@bitergia.com"

USER root

COPY ./docker/worker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/worker-entrypoint.sh

USER sortinghat

ENTRYPOINT ["worker-entrypoint.sh"]
