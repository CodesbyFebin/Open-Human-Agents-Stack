#!/usr/bin/env bash
# Opt-in source checkout only: does NOT import, build, deploy, or enable executables.
set -euo pipefail
if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi
repo_root="$(git rev-parse --show-toplevel)"
destination="${1:-${repo_root}/.upstream-sources}"
mkdir -p "$destination"
destination="$(cd "$destination" && pwd -P)"
# Never place third-party checkouts into tracked core application paths.
case "$destination/" in
  "$repo_root"/.upstream-sources/*) ;;
  *) echo "Use the default repository-local .upstream-sources destination only." >&2; exit 2 ;;
esac
clone_one() {
  local name="$1" url="$2" path="$destination/$1"
  if [ -e "$path" ]; then
    echo "SKIP $name: path exists (no overwrite): $path"
    return
  fi
  git clone --depth 1 --filter=blob:none -- "$url" "$path"
  printf '%s %s\n' "$name" "$(git -C "$path" rev-parse HEAD)"
}
echo "Inspect third-party licenses before any redistribution."
clone_one octop https://github.com/TencentCloud/Octop.git
clone_one openhuman https://github.com/tinyhumansai/openhuman.git
clone_one andee https://github.com/kuafuai/andee.git
echo "Done: upstream checkouts are local-only, ignored by git, and NOT merged into OpenMinds."
