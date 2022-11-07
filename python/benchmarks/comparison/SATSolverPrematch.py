from mapf_branch_and_bound.bbsolver import solve_bb
from mapfmclient import Problem as cProblem, Solution
from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Glucose3

from python.algorithm import MapfAlgorithm
from python.benchmarks.comparison.MDD import MDD
from python.benchmarks.comparison.util import convert_grid_dict_ints, dijkstra_distance


class SATSolver(MapfAlgorithm):

    n_agents: int
    graph: dict
    heuristics: list
    min_makespan: int
    starts: list
    goals: list
    delta: int
    mdd: dict

    def solve(self, problem: cProblem) -> Solution:
        res = solve_bb(problem, self.solve_internal)
        return res

    def solve_internal(self, problem: cProblem, bound) -> Solution:
        self.n_agents = len(problem.starts)
        self.graph, coord_to_int, int_to_coord = convert_grid_dict_ints(problem.grid)
        self.starts = [None] * self.n_agents
        self.goals = [None] * self.n_agents
        self.heuristics = [None] * self.n_agents
        for start in problem.starts:
            self.starts[start.color] = coord_to_int[start.x, start.y]
        for goal in problem.goals:
            self.goals[goal.color] = coord_to_int[goal.x, goal.y]
        distances = {}
        for vertex in self.goals:
            distances[vertex] = dijkstra_distance(self.graph, vertex)
        for i in range(self.n_agents):
            self.heuristics[i] = distances[self.goals[i]][self.starts[i]]
        self.min_makespan = max(self.heuristics)
        self.mdd = {}
        for a in range(self.n_agents):
            self.mdd[a] = MDD(self.graph, a, self.starts[a], self.goals[a], self.min_makespan)
        self.delta = 0
        paths = self.solve_cnf()
        for path in paths:
            for i, loc in enumerate(path):
                path[i] = int_to_coord[loc]
        return Solution.from_paths(paths)

    def solve_cnf(self):
        while True:
            mu = self.min_makespan + self.delta
            for a in range(self.n_agents):
                if self.delta > 0:
                    self.mdd[a] = MDD(self.graph, a, self.starts[a], self.goals[a], mu, self.mdd[a])
            cnf, convert = self.generate_cnf(mu)
            solver = Glucose3()
            solver.append_formula(cnf)
            print("start solving")
            solver.solve()
            if solver.get_model() is not None:
                break
            self.delta += 1
        path = set()
        for clause in solver.get_model():
            if clause in convert:
                path.add(convert[clause])
        res = [[] for _ in range(self.n_agents)]
        for key in sorted(path, key=lambda x: (x[0], x[2])):
            res[key[2]].append(key[1])
        return res

    @property
    def name(self) -> str:
        return "SAT-MAPFM-Prematch"

    def generate_cnf(self, upperbound):
        cnf = CNF()
        index = 0
        T = range(upperbound)
        vertices = {}
        edges = {}
        costs = {}
        mdd_vertices = {}
        mdd_edges = {}
        for a in range(self.n_agents):
            mdd_vertices[a] = {}
            mdd_vertices[a][upperbound] = {self.goals[a]}
            mdd_edges[a] = {}
            for t in T:
                mdd_vertices[a][t] = set()
                mdd_edges[a][t] = set()
            for key, value in self.mdd[a].mdd.items():
                j, t = key
                vertices[t, j, a] = index = index + 1
                mdd_vertices[a][t].add(j)
                for nbr in value:
                    k = nbr[0]
                    mdd_edges[a][t].add((j, k))
                    edges[t, j, k, a] = index = index + 1
                    if t >= self.heuristics[a] and (j != k or j != self.goals[a]):
                        costs[t, a, j, k] = index = index + 1
        # Start / End
        for a in range(self.n_agents):
            cnf.append([vertices[0, self.starts[a], a]])
            vertices[upperbound, self.goals[a], a] = index = index + 1
            cnf.append([vertices[upperbound, self.goals[a], a]])
        # Constraints
        for a in range(self.n_agents):
            for t in T:
                # No two agents at a vertex at timestep t
                cnf.extend(
                    CardEnc.atmost(lits=[vertices[t, key, a] for key in mdd_vertices[a][t]], top_id=cnf.nv, bound=1))
                for j in mdd_vertices[a][t]:
                    # 1
                    cnf.append([-vertices[t, j, a]] + [edges[t, j, l, a] for k, l in mdd_edges[a][t] if j == k])
                for j, k in mdd_edges[a][t]:
                    # 3
                    cnf.append([-edges[t, j, k, a], vertices[t, j, a]])
                    cnf.append([-edges[t, j, k, a], vertices[t + 1, k, a]])
                    if j != k:
                        # 4 edited so the edges must be empty
                        for a2 in range(self.n_agents):
                            if a != a2 and (k, j) in mdd_edges[a2][t]:
                                cnf.append([-edges[t, j, k, a], -edges[t, k, j, a2]])
                for a2 in range(self.n_agents):
                    if a != a2:
                        for j in mdd_vertices[a][t]:
                            # 5
                            if j in mdd_vertices[a2][t]:
                                cnf.append([-vertices[t, j, a], -vertices[t, j, a2]])
                if t >= self.heuristics[a]:
                    for j, k in mdd_edges[a][t]:
                        # 6
                        if (t, a, j, k) in costs:
                            cnf.append([-edges[t, j, k, a], costs[t, a, j, k]])
        cardinality = CardEnc.atmost(lits=[costs[key] for key in costs], top_id=cnf.nv,
                                     bound=self.delta)
        cnf.extend(cardinality.clauses)
        return cnf, {v: k for k, v in vertices.items()}