#!/bin/bash
set -ex

VERSION="1.0.2"

./build_release.sh

docker build -t aethertaberu/sub-cache:$VERSION .
docker tag aethertaberu/sub-cache:$VERSION aethertaberu/sub-cache:latest
docker push aethertaberu/sub-cache:$VERSION
docker push aethertaberu/sub-cache:latest
