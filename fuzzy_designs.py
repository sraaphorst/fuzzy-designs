# fuzzy_designs.py
# By Sebastian Raaphorst, 2023.

from fractions import Fraction
from itertools import combinations
import logging
from math import comb
from sys import argv
from typing import Dict, FrozenSet, Optional, Tuple

from ortools.linear_solver import pywraplp

Block = FrozenSet[int]
FuzzyDesign = Dict[Block, Fraction]
Solution = Tuple[Fraction, FuzzyDesign]


def create_logger(name: str, level: int = logging.WARNING) -> logging.Logger:
    """
    Create a Logger to be used for logging, configured with the given name, which should be the class
    or module from where the logging is being done.

    The format of the output will be: time - name - level - message

    Args:
        name (str): the name of the module or class in which the logger will be used
        level (int): the logging level; values should be taken from the Python logging module

    Returns:
        a configured Logger that can be used for logging
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


_logger = create_logger('fuzzy_designs', logging.INFO)


def find_tvkl_fuzzy_design(t: int, v: int, k: int, lmb: int = 1) -> Optional[Solution]:
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
    """
    points = frozenset(range(v))
    potential_blocks = frozenset(frozenset(b) for b in combinations(points, k))
    tuples = frozenset(frozenset(p) for p in combinations(points, t))

    # Formulate the problem as an LP.
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        raise ValueError('Could not create solver.')

    # Create variables for all the blocks.from
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


def main() -> None:
    executable = argv[0]
    try:
        t, v, k, lmb = map(int, argv[1:])
    except ValueError as ex:
        print(f'Usage: {executable} t v k lambda')
        print(f'Exception occurred: {ex}')

    try:
        solution_size, fuzzy_design = find_tvkl_fuzzy_design(t, v, k, lmb)
        if fuzzy_design is not None:
            print(f'Solution size: {solution_size} over {len(fuzzy_design)} blocks.')
            print()
            print('*** FUZZY BLOCKS ***')
            sorted_fuzzy_design = [(b, f) for b, f in sorted(fuzzy_design.items(), key=lambda x: sorted(x[0]))]
            for block, fuzzy_factor in sorted(fuzzy_design.items(), key=lambda x: sorted(x[0])):
                print(f'{list(sorted(block))} -> {fuzzy_factor}')
            print()
            print('*** COVERAGES ***')
            for tup in combinations(range(v), t):
                tup_set = set(tup)
                covering_blocks = [(b, f) for b, f in sorted_fuzzy_design if tup_set.issubset(b)]
                factor_string = ' + '.join(f'{f} * {list(b)}' for b, f in covering_blocks)
                sum_string = str(sum(f for _, f in covering_blocks))
                print(f'{list(tup)}: {factor_string} = {sum_string}')
        else:
            print(f'Could not find a {t}-({v}, {k}, {lmb}) fuzzy design.')
    except ValueError as ex:
        print(f'Exception occurred: {ex}')


if __name__ == '__main__':
    main()
