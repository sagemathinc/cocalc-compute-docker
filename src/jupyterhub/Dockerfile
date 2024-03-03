ARG MICROK8S_TAG=
ARG ARCH=
FROM sagemathinc/microk8s${ARCH}:${MICROK8S_TAG}

USER root

COPY install-jupyterhub.conf /etc/supervisor/conf.d/

RUN mkdir -p /jupyterhub
COPY install-jupyterhub.sh /jupyterhub/install-jupyterhub.sh
COPY ingress.yaml /jupyterhub/ingress.yaml
RUN chmod a+x /jupyterhub/install-jupyterhub.sh
RUN chown user:user -R /jupyterhub

WORKDIR /home/user
USER user

