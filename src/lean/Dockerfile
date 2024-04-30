ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

# Install VS Code
USER root
RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN chown -R user:user /usr/local

USER user

# INSTEAL LEAN VS Code extension
RUN code-server --install-extension leanprover.lean4

# Install LEAN
# See https://github.com/leanprover/elan?tab=readme-ov-file#manual-installation
RUN \
     cd /home/user \
  && curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf > elan-init.sh \
  && chmod +x elan-init.sh \
  && ./elan-init.sh -y \
  && cp -rv /home/user/.elan/* /usr/local/ \
  && rm -rf /home/user/.elan elan-init.sh \
  && elan default stable






