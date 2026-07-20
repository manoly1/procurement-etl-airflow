# checkpoints — "did the real system actually build?" checks

Each module ends with `make checkpoint N`, which runs `check_module_NN.py`
against the real machine (tool versions, containers, rows in Postgres, DAG run
status) and prints a line-by-line report ending in:

    STATUS: PASSED
    STATUS: FAILED

This is the same contract as the original VBA `Logger.bas` / Power Automate
flow: either everything is green, or it is visible which line is red. A browser
cannot check Docker or Postgres, so this is where the guide's interactive cells
hand off to the real system.

Run, for example:

    make checkpoint 0
