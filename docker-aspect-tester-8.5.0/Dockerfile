FROM dealii/dealii:v8.5.0-gcc-mpi-fulldepscandi-debugrelease

MAINTAINER timo.heister@gmail.com

USER root
ADD script.sh script.sh

RUN chown $USER:$USER *.sh
USER $USER

RUN chmod u+x *.sh
CMD ./script.sh
