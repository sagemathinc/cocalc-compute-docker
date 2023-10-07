ARG ARCH=

FROM sagemathinc/compute-base${ARCH}

COPY start.js /cocalc/src/compute/compute

RUN chmod a+rwx /cocalc/src/compute/compute/start.js

USER user

CMD cd /cocalc/src/compute/compute && node start.js

