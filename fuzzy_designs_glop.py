# fuzzy_designs_glop.py
# By Sebastian Raaphorst, 2023.
#
# Simply satisfy the t-set coverage property.

from math import comb
from typing import Optional

from ortools.linear_solver import pywraplp

from common import *

_logger = create_logger('fuzzy_designs', logging.INFO)


def find_csp_fuzzy_design(t: int, v: int, k: int, lmb: int = 1) -> Optional[Solution]:
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

    This simply amounts of solving an LP, so we use GLOP.
    """
    points = frozenset(range(v))
    potential_blocks = frozenset(frozenset(b) for b in combinations(points, k))
    tuples = frozenset(frozenset(p) for p in combinations(points, t))

    # Formulate the problem as an LP.
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        raise ValueError('Could not create solver.')

    # Create variables for all the blocks.
    block_variables = {b: solver.NumVar(0, lmb, str(b)) for b in potential_blocks}
    _logger.info(f'Created {len(block_variables)} variables.')

    # Add a constraint for each set to cover.
    constraints = []
    for tup in tuples:
        ct = solver.Constraint(lmb, lmb, str(tup))
        for block, variable in block_variables.items():
            ct.SetCoefficient(variable, 1 if tup.issubset(block) else 0)
        constraints.append(ct)
    _logger.info(f'Created {len(constraints)} constraints.')

    # Formulate objective function to pick the minimum number of blocks.
    # Note that this just guarantees satisfiability, and does not impose issue values on the blocks.
    objective = solver.Objective()
    for variable in block_variables.values():
        objective.SetCoefficient(variable, 1)
    objective.SetMinimization()

    # Calculate the required solution size.
    solution_size = Fraction(lmb * comb(v, t) / comb(k, t)).limit_denominator()
    _logger.info(f'Expected solution size: {solution_size}')

    # Solve and check size.
    solver.Solve()
    obj_value = Fraction(objective.Value()).limit_denominator()
    if obj_value != solution_size:
        _logger.warning(f'Solution of size {obj_value} found, expected: {solution_size}')
        return None

    return solution_size, {b: s
                           for b, v in block_variables.items()
                           if (s := Fraction(v.solution_value()).limit_denominator())}


if __name__ == '__main__':
    main(find_csp_fuzzy_design)
