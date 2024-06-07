#! /usr/bin/env bash

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="${SCRIPT_PATH%llm-assistant*}llm-assistant"

pushd "${PROJECT_PATH}" >/dev/null
python -m doctest docs/*.md
popd >/dev/null
