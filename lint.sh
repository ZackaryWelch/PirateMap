#!/usr/bin/env bash
.venv/bin/ruff check --select ALL --ignore ANN,Q000,D1,D203,D212,S311,TRY002,E501 --fix
