ARG SAGEMATH_VERSION
ARG ARCH=
FROM sagemathinc/sagemath-core${ARCH}:${SAGEMATH_VERSION} AS base

COPY optional/install.sh /tmp
RUN chmod a+x /tmp/install.sh
RUN apt-get update && apt-get install -y automake

RUN /tmp/install.sh 4ti2
RUN /tmp/install.sh admcycles
RUN /tmp/install.sh benzene
RUN /tmp/install.sh biopython
RUN /tmp/install.sh bliss
RUN /tmp/install.sh buckygen
RUN /tmp/install.sh cbc
RUN /tmp/install.sh coxeter3
RUN /tmp/install.sh cryptominisat
RUN /tmp/install.sh csdp
RUN /tmp/install.sh cunningham_tables
#RUN /tmp/install.sh cylp
RUN /tmp/install.sh d3js
RUN /tmp/install.sh database_cremona_ellcurve
RUN /tmp/install.sh database_cubic_hecke
RUN /tmp/install.sh database_jones_numfield
RUN /tmp/install.sh database_knotinfo
RUN /tmp/install.sh database_kohel
RUN /tmp/install.sh database_mutation_class
RUN /tmp/install.sh database_odlyzko_zeta
RUN /tmp/install.sh database_stein_watkins
RUN /tmp/install.sh database_symbolic_data
RUN /tmp/install.sh debugpy
RUN /tmp/install.sh dot2tex
RUN /tmp/install.sh dsdp
RUN /tmp/install.sh e_antic
RUN /tmp/install.sh ecos_python
#RUN /tmp/install.sh ffmpeg
RUN /tmp/install.sh fricas
RUN /tmp/install.sh frobby
RUN /tmp/install.sh gap_jupyter
RUN /tmp/install.sh gap_packages
RUN /tmp/install.sh gitpython
RUN /tmp/install.sh glucose
#RUN /tmp/install.sh gp2c
#RUN /tmp/install.sh graphviz
RUN /tmp/install.sh igraph
#RUN /tmp/install.sh ImageMagick
RUN /tmp/install.sh ipympl
#RUN /tmp/install.sh isl
#RUN /tmp/install.sh jupymake
RUN /tmp/install.sh jupyterlab
RUN /tmp/install.sh kenzo
RUN /tmp/install.sh kissat
RUN /tmp/install.sh latte_int
#RUN /tmp/install.sh libgraphviz
#RUN /tmp/install.sh libjpeg
RUN /tmp/install.sh libnauty
RUN /tmp/install.sh libogg
RUN /tmp/install.sh libsemigroups
#RUN /tmp/install.sh libxml2
RUN /tmp/install.sh lidia
RUN /tmp/install.sh lrslib
RUN /tmp/install.sh mathics
RUN /tmp/install.sh mathics_scanner
RUN /tmp/install.sh mcqd
RUN /tmp/install.sh meataxe
#RUN /tmp/install.sh p_group_cohomology
RUN /tmp/install.sh mpfrcx
RUN /tmp/install.sh msolve
RUN /tmp/install.sh nibabel
#RUN /tmp/install.sh normaliz
RUN /tmp/install.sh notedown
RUN /tmp/install.sh onetbb
#RUN /tmp/install.sh ore_algebra
RUN /tmp/install.sh osqp_python
#RUN /tmp/install.sh p_group_cohomology
RUN /tmp/install.sh palettable
#RUN /tmp/install.sh pandoc
#RUN /tmp/install.sh pandoc_attributes
RUN /tmp/install.sh papilo
RUN /tmp/install.sh pari_elldata
RUN /tmp/install.sh pari_galpol
#RUN /tmp/install.sh pari_jupyter
RUN /tmp/install.sh pari_nftables
RUN /tmp/install.sh pari_seadata
#RUN /tmp/install.sh pdf2svg
#RUN /tmp/install.sh perl_cpan_polymake_prereq
#RUN /tmp/install.sh perl_mongodb
RUN /tmp/install.sh perl_term_readline_gnu
RUN /tmp/install.sh phitigra
RUN /tmp/install.sh pint
RUN /tmp/install.sh plantri
#RUN /tmp/install.sh polymake
#RUN /tmp/install.sh hypersurfaces
# omitting polytopes_db_4d because it is "huge" (though I have no idea how big!?)
# RUN /tmp/install.sh polytopes_db_4d
RUN /tmp/install.sh pybtex
RUN /tmp/install.sh pycosat
RUN /tmp/install.sh pycryptosat
#RUN /tmp/install.sh pygraphviz
#RUN /tmp/install.sh pynormaliz
#RUN /tmp/install.sh pyscipopt
RUN /tmp/install.sh pysingular
RUN /tmp/install.sh pytest
RUN /tmp/install.sh pytest_mock
RUN /tmp/install.sh pytest_xdist
RUN /tmp/install.sh python_build
RUN /tmp/install.sh python_igraph
RUN /tmp/install.sh pyx
RUN /tmp/install.sh qdldl_python
#RUN /tmp/install.sh r
#RUN /tmp/install.sh retrolab
#RUN /tmp/install.sh rst2ipynb
RUN /tmp/install.sh rubiks
RUN /tmp/install.sh saclib
#RUN /tmp/install.sh sage_flatsurf
#RUN /tmp/install.sh sage_numerical_backends_coin
#RUN /tmp/install.sh sage_numerical_backends_cplex
#RUN /tmp/install.sh sage_numerical_backends_gurobi
RUN /tmp/install.sh sage_sws2rst
RUN /tmp/install.sh scip
RUN /tmp/install.sh scip_sdp
RUN /tmp/install.sh scs
RUN /tmp/install.sh singular_jupyter
RUN /tmp/install.sh sirocco
RUN /tmp/install.sh slabbe
RUN /tmp/install.sh snappy
RUN /tmp/install.sh soplex
RUN /tmp/install.sh sqlalchemy
#RUN /tmp/install.sh surface_dynamics
RUN /tmp/install.sh symengine
RUN /tmp/install.sh tdlib
RUN /tmp/install.sh texlive
RUN /tmp/install.sh texttable
RUN /tmp/install.sh tides
RUN /tmp/install.sh topcom

# Clean up artifacts that we don't need for runtime
RUN cd /usr/local/sage \
  && make misc-clean \
  && rm -rf upstream/ src/doc/output/doctrees/

# Strip binaries -- this saves gigabytes of space and takes a while...
RUN cd /usr/local/sage \
  && LC_ALL=C find local/lib local/bin -type f -exec strip '{}' ';' 2>&1 | grep -v "File format not recognized" |  grep -v "File truncated" || true

# Save more space:
RUN rm -rf /usr/local/sage/build/pkgs/sagelib/src/build

# And delete git repo stuff if it is there.
RUN rm -rf /usr/local/sage/.git

# Now use multisage build to squash all the images into one, so the
# result is much smaller (otherwise nothing
# we deleted above is really gone):
FROM ubuntu:22.04
USER root

COPY --from=base /usr/local/sage /usr/local/sage

# Install packages again, so users can build cython code, etc.
# Sage assumed these exist when it was built so they better be here.
COPY scripts/install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh

# Add links
COPY scripts/links-to-sage.sh /root
RUN chmod +x  /root/links-to-sage.sh && ./root/links-to-sage.sh && rm /root/links-to-sage.sh

