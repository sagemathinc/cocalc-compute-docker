ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

# Install VS Code
USER root
RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN chown -R user:user /usr/local

USER user

ENV ELAN_HOME=/usr/local/
ENV XDG_DATA_HOME=/usr/local

# Install/update the LEAN vs code extension.  It gets installed
# into /usr/local because of the XDG_DATA_HOME env var.
# See https://coder.com/docs/code-server/latest/FAQ#where-are-extensions-stored
RUN code-server --install-extension leanprover.lean4

# Install LEAN
# See https://github.com/leanprover/elan?tab=readme-ov-file#manual-installation
RUN \
     cd /home/user \
  && curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf > elan-init.sh \
  && chmod +x elan-init.sh \
  && ./elan-init.sh -y \
  && rm ./elan-init.sh






