# fuzzy_designs_min.py
# By Sebastian Raaphorst, 2023.
#
# 1. Satisfy the t-coverage property; and
# 2. Minimize the number of blocks included in the final solution by using MIP.

from typing import Optional

from ortools.linear_solver import pywraplp

from common import *


_logger = create_logger('fuzzy_designs', logging.INFO)


def find_min_fuzzy_design(t: int, v: int, k: int, lmb: int = 1) -> Optional[Solution]:
    """
    Given the values t, v, k, and lambda, find a fuzzy design:
    1. Let V be the set of points, i.e. V = {0, ..., v-1}.
    2. Let B be the possible block set, i.e. B = V choose k (all k-subsets of V).
    3. Let T be the set to cover, i.e. T = V choose t (all t-subsets of V).

    If a fuzzy design exists, it is essentially a function d: B -> [0,lmb].
    The fuzzy design will satisfy the properties:
    For every S in T, the subset of C of B containing S will have:

    sum_{c in C} d(c) = lmb.

    If such a fuzzy design can be found, the function will be returned as a Dict, where
    the keys of the Dict will be the blocks b with nonzero values d(b), and the values will be
    the values of d(b).

    Additionally, we want to minimize the number of blocks included in the design.
    This necessitates a MIP instead of an LP, so we use CBC instead of GLOP, and we use multiple processors.
    """
    points = frozenset(range(v))
    potential_blocks = frozenset(frozenset(b) for b in combinations(points, k))
    tuples = frozenset(frozenset(p) for p in combinations(points, t))

    # Formulate the problem as an LP.
    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        raise ValueError('Could not create solver.')

    # Create variables for all the blocks. These map
    block_variables = {b: solver.NumVar(0, lmb, f'b_{b}') for b in potential_blocks}
    _logger.info(f'Created {len(block_variables)} block variables.')

    # Create the indicator variables (which are constrained to integer values) to determine if a block
    # is in the design or not.
    indicator_variables = {b: solver.IntVar(0, 1, f'x_{b}') for b in potential_blocks}
    _logger.info(f'Created {len(indicator_variables)} indicator variables.')

    # Add a constraint for each set to cover.
    num_tup_constraints = 0
    for tup in tuples:
        ct = solver.Constraint(lmb, lmb, f'c_{tup}')
        for block, variable in block_variables.items():
            ct.SetCoefficient(variable, 1 if tup.issubset(block) else 0)
        num_tup_constraints += 1
    _logger.info(f'Created {num_tup_constraints} t-coverage constraints.')

    # Now add constraints on the indicator variables.
    # If b > 0, then indicator variable x = 1.
    # If b = 0, then indicator variable x = 0.
    # The second will be forced by the objective function and this being a minimization problem.
    num_ind_constraints = 0
    for b in potential_blocks:
        bb = block_variables[b]
        xb = indicator_variables[b]
        solver.Add(xb >= bb)
        num_ind_constraints += 1
    _logger.info(f'Created {num_ind_constraints} block indicator constraints')

    # Formulate objective function to pick the minimum number of blocks possible to solve the problem,
    # regardless of what uniform coefficients each block has.
    objective = solver.Objective()
    for x in indicator_variables.values():
        objective.SetCoefficient(x, 1)
    objective.SetMinimization()
    solver.Solve()
    obj_value = Fraction(objective.Value()).limit_denominator()

    return obj_value, {b: s
                       for b, v in block_variables.items()
                       if (s := Fraction(v.solution_value()).limit_denominator())}


if __name__ == '__main__':
    main(find_min_fuzzy_design)
