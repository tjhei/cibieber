#!/bin/bash

if [[ -z "$1" || -z "$2" ]] ; then
    echo "usage: $0 <duration> <cmd>"
    echo '  <duration>: floating point number in seconds, optionally add "m" for minutes, "h" for hours.'
    echo '  <cmd>: docker arguments (stuff that comes after "docker run")'
    exit 0
fi

to=$1
shift

cont=$(docker run -d "$@")
ret=$?
if [ $ret -ne 0 ]; then
    echo "docker run failed with status $ret"
    echo "the command executed was:"
    echo "docker run -d \"$@\""
    exit 2
fi
code=$(timeout "$to" docker wait "$cont" || true)

docker kill $cont &> /dev/null
docker logs $cont

docker rm $cont &> /dev/null
if [ -z "$code" ]; then
    echo "timeout encountered!"
    exit 1
fi
#echo "status: $code"
exit $code
