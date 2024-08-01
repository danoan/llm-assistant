#! /usr/bin/env bash

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pushd "${SCRIPT_PATH}" >/dev/null
PYNPUT_BACKEND_KEYBOARD=uinput sudo -E ./../.venv/bin/llm-assistant session
popd >/dev/null
