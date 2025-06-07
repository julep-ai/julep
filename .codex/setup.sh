#!/usr/bin/env bash
#
# setup-all.sh ─ one-shot bootstrap for the whole julep monorepo
#
# › run from repo root:  ./setup-all.sh
#
# It will:
#   • ensure Poetry + TypeSpec compiler are available
#   • iterate over each top-level directory and install deps:
#       – pyproject.toml  ➜  poetry install
#       – package.json    ➜  npm install  (uses pnpm if present)
#       – requirements.txt➜  pip install -r
#   • install root pre-commit hooks (if .pre-commit-config.yaml exists)
#   • stop on first error (set -e)

set -euo pipefail

### 1. Globals --------------------------------------------------------------

IGNORE_DIRS_DEFAULT="sdks deploy scripts monitoring .git .venv node_modules"
IGNORE_DIRS="${IGNORE_DIRS:-$IGNORE_DIRS_DEFAULT}"

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# cd "$ROOT_DIR"

RED="\033[0;31m"; GREEN="\033[0;32m"; CYAN="\033[0;36m"; NC="\033[0m"

announce() { echo -e "${CYAN}==>$1${NC}"; }

### 3. Ensure TypeSpec compiler --------------------------------------------

if ! command -v tsp &> /dev/null; then
  announce "Installing TypeSpec compiler globally (npm)…"
  npm install -g @typespec/compiler > /dev/null
else
  announce "TypeSpec compiler present → $(tsp --version)"
fi

announce "Installing hasura-cli globally (npm)…"
curl -L https://github.com/hasura/graphql-engine/raw/stable/cli/get.sh | bash

### 4. Walk directories -----------------------------------------------------
curl -LsSf https://astral.sh/uv/install.sh | sh


if [[ -f "pyproject.toml" ]]; then
  announce "Installing root deps"
  uv sync
  echo -e "${GREEN}✓ root deps installed${NC}"
fi


OIFS=$IFS; IFS=$'\n'
for dir in $(git ls-tree --name-only -d HEAD | sort); do
  d="${dir#./}"
  if [[ " $IGNORE_DIRS " =~ [[:space:]]"$d"[[:space:]] ]]; then
    echo -e "· skipping $d (ignored)"
    continue
  fi

  announce "Processing $d/"

  # uv project?
  if [[ -f "$d/pyproject.toml" ]]; then
    pushd "$d" > /dev/null
    announce "[uv] installing in $d …"
    uv sync
    uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
    popd > /dev/null
    echo -e "${GREEN}✓ uv install done for $d${NC}"
    continue
  fi

  # Node project?
  if [[ -f "$d/package.json" ]]; then
    pushd "$d" > /dev/null
    announce "[npm] installing in $d …"
    if command -v pnpm &> /dev/null; then
      pnpm install --silent
    else
      npm install --silent
    fi
    popd > /dev/null
    echo -e "${GREEN}✓ npm install done for $d${NC}"
    continue
  fi

  # Plain requirements.txt?
  if [[ -f "$d/requirements.txt" ]]; then
    pushd "$d" > /dev/null
    announce "[pip] installing requirements in $d …"
    pip install -r requirements.txt
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
    popd > /dev/null
    echo -e "${GREEN}✓ pip install done for $d${NC}"
    continue
  fi

  echo -e "· no recognised manifest in $d – nothing to install"
done
IFS=$OIFS

### 5. Pre-commit -----------------------------------------------------------

if [[ -f ".pre-commit-config.yaml" ]]; then
  announce "Installing git pre-commit hooks…"
  pip install --quiet pre-commit
  pre-commit install
  echo -e "${GREEN}✓ pre-commit hooks installed${NC}"
fi

echo -e "${GREEN}\nAll done – monorepo dependencies ready!${NC}"
