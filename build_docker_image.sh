#!/bin/bash
set -ex

VERSION="test"

docker build -t aethertaberu/sub-cache:$VERSION .
