#!/bin/bash
set -ex

pushd web
npm install
npm ci
npm run build
popd

pdm build_release
