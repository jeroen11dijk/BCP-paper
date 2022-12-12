#!/bin/bash

repo=/data/BCP-paper
#PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/comparison_25percent_1teams.py
#PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/comparison_25percent_3teams.py
#PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/comparison_25percent_6teams.py
#PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/comparison_25percent_12teams.py
#PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/comparison_warehouse.py
PYTHONPATH=$repo:$PYTHONPATH python3.9 $repo/python/benchmarks/main.py
