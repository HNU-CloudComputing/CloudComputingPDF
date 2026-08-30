#!/usr/bin/env bash
set -euo pipefail

cd CCBook

xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex

test -s main.pdf
