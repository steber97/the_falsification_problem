from pysat.solvers import Glucose4
from typing import List

class CnfSAT:
    def __init__(self, clauses: List[int]):
        # integers with positive or negative values.
        self.clauses = clauses

    def to_glucose(self) -> Glucose4:
        cnf = Glucose4()
        for clause in self.clauses:
            cnf.add_clause(clause)
        return cnf
    
    def __str__(self) -> str:
        return str(self.clauses)