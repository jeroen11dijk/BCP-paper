import logging

from mapfmclient import Problem

from python.benchmarks.comparison.src.cbm.cbm_low_level import CBMLowLevelSolver
from python.benchmarks.comparison.src.cbm.cbm_paths import CBMMakespanFullSolution
from python.benchmarks.comparison.src.ctnode import CTNode
from python.benchmarks.comparison.src.data.constraint_tree import ConstraintTree
from python.benchmarks.comparison.src.high_level import HighLevelSolver
from python.benchmarks.comparison.src.paths import FullSolution


class CBMHighLevelSolver(HighLevelSolver):
    def __init__(self, low_level_solver: CBMLowLevelSolver, problem: Problem):
        super().__init__(low_level_solver, problem)
        self.low_level_solver = low_level_solver

    def solve(self, root: CTNode) -> FullSolution:
        sol: CBMMakespanFullSolution = super().solve(root)

        sic = sum(map(lambda p: len(p[1]), sol.get_flattened_paths()))
        delta = sic - self.low_level_solver.sic_lb
        self.low_level_solver.delta = delta

        self.OPEN.queue.clear()

        constraint_tree = ConstraintTree(0, None)
        new_root = CTNode(set(), constraint_tree)

        solution = super().solve(new_root)
        logging.info("Found solution!")
        return solution
