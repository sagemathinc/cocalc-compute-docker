ARG ARCH=

FROM sagemathinc/compute-base${ARCH}

COPY start.js /cocalc/src/compute/compute

USER user

CMD cd /cocalc/src/compute/compute && node start.js

