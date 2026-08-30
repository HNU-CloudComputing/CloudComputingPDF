#!/usr/bin/env bash
set -euo pipefail

: "${CHAPTER_KEY:?CHAPTER_KEY is required}"
: "${CHAPTER_REL_PATH:?CHAPTER_REL_PATH is required}"

if [[ ! "$CHAPTER_KEY" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "Invalid chapter key: $CHAPTER_KEY" >&2
  exit 2
fi

if [[ ! "$CHAPTER_REL_PATH" =~ ^[A-Za-z0-9_./-]+$ ]] || [[ "$CHAPTER_REL_PATH" == *".."* ]]; then
  echo "Invalid chapter path: $CHAPTER_REL_PATH" >&2
  exit 2
fi

cd CCBook

if [[ ! -f "${CHAPTER_REL_PATH}.tex" ]]; then
  echo "Chapter source does not exist: ${CHAPTER_REL_PATH}.tex" >&2
  exit 2
fi

mkdir -p generated_chapters
chapter_driver="generated_chapters/gen_${CHAPTER_KEY}.tex"

printf '%s\n' \
  '\input{preamble.tex}' \
  '\begin{document}' \
  "\\input{${CHAPTER_REL_PATH}}" \
  '\end{document}' > "$chapter_driver"

xelatex \
  -interaction=nonstopmode \
  -halt-on-error \
  -file-line-error \
  -jobname="gen_${CHAPTER_KEY}" \
  "$chapter_driver"

test -s "gen_${CHAPTER_KEY}.pdf"
