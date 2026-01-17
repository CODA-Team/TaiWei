#!/usr/bin/env bash
function __setpaths() {
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  echo "Setting FLOW_HOME to $DIR"
  export FLOW_HOME=$DIR
}
__setpaths
