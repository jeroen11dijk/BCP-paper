#include <fstream>
#include <iostream>
#include <unordered_set>

#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/exterior_property.hpp>
#include <boost/graph/floyd_warshall_shortest.hpp>
#include <boost/graph/graphviz.hpp>

class ShortestPathHeuristic {
 public:
  ShortestPathHeuristic(size_t dimx, size_t dimy,
                        const std::unordered_set<Location>& obstacles, const std::vector<std::unordered_set<Location>>& goals)
      : m_shortestDistance(dimy*dimx, std::vector<int>(dimy*dimx, INT_MAX)), m_dimx(dimx), m_dimy(dimy) {
    std::vector<int> xMoves {INT_MAX, 0,0,+1,-1};
    std::vector<int> yMoves {INT_MAX, +1,-1,0,0};
    for (size_t i = 0; i < goals.size(); ++i) {
      for (const auto& goal : goals[i]) {
        m_shortestDistance[locToVert(goal)][locToVert(goal)] = 0;
        std::priority_queue<std::vector<int>, std::vector<std::vector<int>>, std::greater<std::vector<int>>> minheap;
        minheap.push({0, goal.x, goal.y});

        while(minheap.size()) {
          auto curr = minheap.top();
          minheap.pop();
          int currDist = curr[0]; int x = curr[1]; int y = curr[2];
          for (int d=1;d<=4;d++){
            int newX = x + xMoves[d];
            int newY = y + yMoves[d];
            int newDist = currDist + 1;
            Location loc(newX, newY);
            if (obstacles.find(loc) == obstacles.end()) {
              if (newX > -1 && newX < dimx && newY > -1 && newY < dimy) {
                if (newDist < m_shortestDistance[locToVert(goal)][locToVert(loc)]) {
                  m_shortestDistance[locToVert(goal)][locToVert(loc)] = newDist;
                  m_shortestDistance[locToVert(loc)][locToVert(goal)] = newDist;
                  minheap.push({newDist, newX, newY});
                }
              }
            }
          }

        }

      }
    }
  }

  int getValue(const Location& a, const Location& b) {
    int idx1 = locToVert(a);
    int idx2 = locToVert(b);
    return (m_shortestDistance)[idx1][idx2];
  }

 private:
  int locToVert(const Location& l) const { return l.x + m_dimx * l.y; }

  Location idxToLoc(size_t idx) {
    int x = idx % m_dimx;
    int y = idx / m_dimx;
    return Location(x, y);
  }

 private:
  std::vector<std::vector<int>> m_shortestDistance;
  size_t m_dimx;
  size_t m_dimy;
};
