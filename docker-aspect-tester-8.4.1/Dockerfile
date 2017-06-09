FROM tjhei/dealii-clang:v8.4.1

MAINTAINER timo.heister@gmail.com

USER root
ADD script.sh script.sh
# ADD generate_reference_output.sh generate_reference_output.sh
RUN chown bob:bob *.sh
USER bob

RUN chmod u+x *.sh
CMD ./script.sh
