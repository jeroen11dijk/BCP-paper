from heapq import heappush, heappop

import numpy as np
from mapfmclient import Problem as cProblem, Solution
from pysat.card import CardEnc
from pysat.formula import CNF
from pysat.solvers import Glucose3
from scipy.optimize import linear_sum_assignment

from MDD import MDD
from python.algorithm import MapfAlgorithm


def convert_grid_dict_ints(graph):
    grap_new = {}
    height = len(graph)
    width = len(graph[0])
    coord_to_int = {}
    int_to_coord = {}
    for i in range(len(graph)):
        for j in range(len(graph[0])):
            if graph[i][j] == 0:
                current = width * i + j
                coord_to_int[(i, j)] = current
                int_to_coord[current] = (i, j)
                neighbours = []
                if i != 0 and graph[i - 1][j] == 0:
                    neighbours.append(width * (i - 1) + j)
                if j != 0 and graph[i][j - 1] == 0:
                    neighbours.append(width * i + j - 1)
                if i != height - 1 and graph[i + 1][j] == 0:
                    neighbours.append(width * (i + 1) + j)
                if j != width - 1 and graph[i][j + 1] == 0:
                    neighbours.append(width * i + j + 1)
                grap_new[current] = neighbours
    return grap_new, coord_to_int, int_to_coord


def dijkstra_distance(G, source):
    dist = {}  # dictionary of final distances
    seen = {source: 0}
    c = 1
    fringe = []  # use heapq with (distance,label) tuples
    heappush(fringe, (0, c, source))
    while fringe:
        (d, _, v) = heappop(fringe)
        if v in dist:
            continue  # already searched this node.
        dist[v] = d
        neighbours = G[v]
        for neighbour in neighbours:
            vw_dist = d + 1
            if neighbour not in seen or vw_dist < seen[neighbour]:
                seen[neighbour] = vw_dist
                c += 1
                heappush(fringe, (vw_dist, c, neighbour))
    return dist


class SATSolverColored(MapfAlgorithm):

    def solve(self, problem: cProblem) -> Solution:
        self.n_agents = len(problem.starts)
        self.graph, coord_to_int, int_to_coord = convert_grid_dict_ints(problem.grid)
        problem_starts = []
        for start in problem.starts:
            color = start.color
            loc = coord_to_int[start.x, start.y]
            if color + 1 > len(problem_starts):
                problem_starts.append([])
            problem_starts[color].append(loc)
        problem_goals = []
        for goal in problem.goals:
            color = goal.color
            loc = coord_to_int[goal.x, goal.y]
            if color + 1 > len(problem_goals):
                problem_goals.append([])
            problem_goals[color].append(loc)
        distances = {}
        for vertex in self.graph:
            distances[vertex] = dijkstra_distance(self.graph, vertex)
        self.options = {}
        self.heuristics = []
        makespans = []
        for team in zip(problem_starts, problem_goals):
            for start in team[0]:
                self.options[start] = team[1]
            starts = team[0]
            goals = team[1]
            matrix = []
            for i, start in enumerate(starts):
                matrix.append([])
                for goal in goals:
                    matrix[i].append(distances[goal][start])
            biadjacency_matrix = np.array(matrix)
            row_ind, col_ind = linear_sum_assignment(biadjacency_matrix)
            opt = biadjacency_matrix[row_ind, col_ind].sum()
            for limit in range(1, 1024):
                matrix = []
                for i, start in enumerate(starts):
                    matrix.append([])
                    for goal in goals:
                        if distances[goal][start] < limit:
                            matrix[i].append(distances[goal][start])
                        else:
                            matrix[i].append(1000000)
                biadjacency_matrix = np.array(matrix)
                row_ind, col_ind = linear_sum_assignment(biadjacency_matrix)
                if row_ind.size > 0 and col_ind.size > 0 and biadjacency_matrix[row_ind, col_ind].sum() == opt:
                    self.heuristics.append(biadjacency_matrix[row_ind, col_ind].sum())
                    makespans.append(max([distances[goals[col_ind[i]]][starts[i]] for i in row_ind]))
                    break
        self.min_makespan = max(makespans)
        self.starts = [item for sublist in problem_starts for item in sublist]
        self.delta = 0
        self.mdd = {}
        for a in range(self.n_agents):
            self.mdd[a] = MDD(self.graph, a, self.starts[a], self.options[self.starts[a]], self.min_makespan)
        paths = self.solve_cnf()
        print(paths)
        for path in paths:
            for i, loc in enumerate(path):
                path[i] = int_to_coord[loc]
        print(paths)

        return Solution.from_paths(paths)

    @property
    def name(self) -> str:
        return "SAT-MAPFM-Inmatch"

    def solve_cnf(self):
        while True:
            mu = self.min_makespan + self.delta
            for a in range(self.n_agents):
                if self.delta > 0:
                    self.mdd[a] = MDD(self.graph, a, self.starts[a], self.options[self.starts[a]], mu, self.mdd[a])
            else:
                cnf, convert = self.generate_cnf(mu)
                solver = Glucose3()
                solver.append_formula(cnf)
                solver.solve()
                if solver.get_model() is not None:
                    break
            self.delta += 1
        path = set()
        for clause in solver.get_model():
            if clause in convert:
                path.add(convert[clause])
        res = [[] for _ in range(mu + 1)]
        for key in sorted(path, key=lambda x: (x[0], x[2])):
            res[key[0]].append(key[1])
        cost = (mu + 1) * self.n_agents
        waiting = {i for i in range(self.n_agents)}
        goals = res[-1]
        for locations in reversed(res):
            for a in range(len(locations)):
                if a in waiting and locations[a] == goals[a]:
                    cost -= 1
                if a in waiting and locations[a] != goals[a]:
                    waiting.remove(a)
        return res

    def generate_cnf(self, upperbound):
        cnf = CNF()
        index = 0
        T = range(upperbound)
        vertices = {}
        edges = {}
        waiting = {}
        mdd_vertices = {}
        mdd_edges = {}
        for a in range(self.n_agents):
            mdd_vertices[a] = {}
            mdd_vertices[a][upperbound] = {goal for goal in self.options[self.starts[a]]}
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
                    if j == k and j in self.options[self.starts[a]]:
                        waiting[t, j, k, a] = index = index + 1
        # Start / End
        for a in range(self.n_agents):
            cnf.append([vertices[0, self.starts[a], a]])
            for goal in self.options[self.starts[a]]:
                vertices[upperbound, goal, a] = index = index + 1
            cnf.append([vertices[upperbound, goal, a] for goal in self.options[self.starts[a]]])
        # Constraints
        for a in range(self.n_agents):
            # No two agents at a vertex at the final timestep
            cnf.extend(CardEnc.atmost(lits=[vertices[upperbound, key, a] for key in mdd_vertices[a][upperbound]],
                                      top_id=cnf.nv, bound=1))
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
                    # If an agent takes an edge add it to time edges so we can minimize it
                    if j == k and j in self.options[self.starts[a]]:
                        cnf.append([-waiting[t, j, k, a], edges[t, j, k, a]])
                        for t2 in range(t, upperbound + 1):
                            cnf.append([-waiting[t, j, k, a], vertices[t2, j, a]])
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
                        if t == upperbound - 1:
                            for j in mdd_vertices[a][upperbound]:
                                # 5
                                if j in mdd_vertices[a2][upperbound]:
                                    cnf.append([-vertices[upperbound, j, a], -vertices[upperbound, j, a2]])
        bound = (self.n_agents * upperbound) - (sum(self.heuristics) + self.delta)
        cardinality = CardEnc.atleast(lits=[waiting[key] for key in waiting], top_id=cnf.nv, bound=bound)
        cnf.extend(cardinality.clauses)
        return cnf, {v: k for k, v in vertices.items()}
