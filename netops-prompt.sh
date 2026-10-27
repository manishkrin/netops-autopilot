#!/usr/bin/env bash

NETOPS_AUTOPILOT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

_netops_autopilot_prompt_path() {
  case "$PWD" in
    "$NETOPS_AUTOPILOT_ROOT")
      printf '../netops-autopilot/'
      ;;
    "$NETOPS_AUTOPILOT_ROOT"/*)
      printf '../netops-autopilot/%s' "${PWD#"$NETOPS_AUTOPILOT_ROOT"/}"
      ;;
    *)
      printf '%s' "$PWD"
      ;;
  esac
}

PS1='[*]─[clab]─[$(_netops_autopilot_prompt_path)] '
