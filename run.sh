#!/bin/sh

docker run --rm --platform linux/amd64 -v ./reports:/app/reports edgar "$@"