#!/usr/bin/python
# By Sebastian Raaphorst, 2023.

import logging
from fractions import Fraction
from itertools import combinations
from sys import argv
from typing import Callable, Dict, FrozenSet, Tuple


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


def main(optimizer: Callable[[int, int, int, int], Solution]) -> None:
    executable = argv[0]
    try:
        t, v, k, lmb = map(int, argv[1:])
    except ValueError as ex:
        print(f'Usage: {executable} t v k lambda')
        print(f'Exception occurred: {ex}')

    try:
        solution_size, fuzzy_design = optimizer(t, v, k, lmb)
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
                factor_string = ' + '.join(f'{f} * {list(sorted(b))}' for b, f in covering_blocks)
                sum_string = str(sum(f for _, f in covering_blocks))
                print(f'{list(tup)}: {factor_string} = {sum_string}')
        else:
            print(f'Could not find a {t}-({v}, {k}, {lmb}) fuzzy design.')
    except ValueError as ex:
        print(f'Exception occurred: {ex}')
