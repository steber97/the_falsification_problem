import argparse
from pysat.solvers import Glucose4, Maplesat
from pysat.formula import CNF
import time
import numpy as np
from typing import Tuple



def solve_from_file(file: str) -> Tuple[bool, float, int, int]:
    """
    Given a file with a cnf formula in it,
    Solve the formula (determine if it is satisfiable or not) and return:

    @param file: filename.
    @returns result: if the formula is satisfiable or not.
    @returns timer: the running time of the solver in seconds.
    @returns clauses: number of clauses.
    @returns vars: number of variables.
    """
    cnf = CNF(file)
    solver = Glucose4()
    for clause in cnf.clauses:
        solver.add_clause(clause)

    now = time.time()
    result = solver.solve()
    timer = time.time() - now
    assert result is not None
    result_bool: bool = result is True
    clauses = solver.nof_clauses()
    assert clauses is not None
    vars = solver.nof_vars()
    assert vars is not None
    return result, timer, clauses, vars
