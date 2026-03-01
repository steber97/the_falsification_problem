import matplotlib.pyplot as plt
from multiprocessing import Pool
import os
import numpy as np
import pandas as pd
import sympy
import time
from typing import Tuple


from factoring.factoring_circuit import FactoringCircuit
from factoring.utils import randprime


np.random.seed(42)


def factor_number_with_glucose4(nbits: int) -> Tuple[float, int, int]:
    """
    Given the size of the prime factors in input (nbits),
    create two random prime numbers a, b of size nbits;
    build a "school method" binary multiplier CNF formula,
    that returns True iff it is given in input 2 integers such that 
    their product is a * b.
    The CNF is satisfiable by construction (the two integers are a and b).
    Solve the formula with Glucose4, and return a Tuple with:
    
    @returns total_time [int]: the time it took Glucose to find a solution, in seconds
    @returns number_of_clauses [int]: the number of clauses of the CNF formula.
    @returns number_of_variables [int]: the number of variables fo the CNF formula.
    """
    # Create two random prime numbers a, b of size nbits.
    a = b = 0
    while a == b:
        a = randprime(2**nbits, 2**(nbits+1))
        b = randprime(2**nbits, 2**(nbits+1))
    assert a != b 
    assert not sympy.isprime(a * b) # a*b is, by construction, not prime.
    
    # Build the "school method" binary multiplier circuit c.
    c = FactoringCircuit(a * b)

    # Convert c into a CNF formula.
    cnf, map = c.toCNF()
    g = cnf.to_glucose()

    # Solve it with Glucose4
    now = time.time()
    solve = g.solve(assumptions=[map[c.get_output_gate().id]])
    total_time = time.time() - now
    assert solve  # Make sure that the circuit is SAT.
    
    # Make sure that the certificate encodes a and b.
    if solve:
        model = g.get_model()
        if not isinstance(model, list):
            raise ValueError("The model is not correct.")
        f1, f2 = c.getFactorsFromCnfAssignment(model, map)
        assert f1 == a or f1 == b
        assert f2 == a or f2 == b
    
    tot_variables = g.nof_vars()
    tot_clauses = g.nof_clauses()
    if not isinstance(tot_clauses, int) or not isinstance(tot_variables, int):
        raise ValueError("The CNF formula has a wrong value of clauses or variables.")
    return total_time, tot_clauses, tot_variables


if __name__ == "__main__":
    if "results" not in  os.listdir('.'):
        os.mkdir('results/')

    repetitions = 20
    rangelow, rangeup = 10, 21  # nbits ranges between rangelow-up.
    res_df = pd.DataFrame(columns=['nbits', 'time', 'variables', 'clauses'])
    for nbits in range(rangelow, rangeup):
        with Pool(10) as pool:
            results = pool.map(factor_number_with_glucose4, [nbits]*repetitions)
        for runtime, clauses, vars in results:
            # Record nbit, running time, variables and clauses.
            res_df.loc[len(res_df)] = [nbits, runtime, vars, clauses]  
    
    # Group results by nbits. Record mean and std.
    res_df.groupby(['nbits']).agg(
        time_avg=('time', 'mean'),
        time_std=('time', 'std'),
        variables_avg=('time', 'mean'),
        variables_std=('variables', 'std'),
        clauses_avg=('clauses', 'mean'),
        clauses_std=('clauses', 'std')).to_csv("results/table_2.csv")

    # Polyfit for the blue dashed intercept.
    data = np.log2([res_df[res_df.nbits==nbits]['time'] for nbits in range(rangelow, rangeup)]).T

    m, b = np.polyfit([nbits for nbits in range(rangelow, rangeup) for rep in range(repetitions)], 
               [data[rep][nbits - rangelow] for nbits in range(rangelow, rangeup) for rep in range(repetitions)],
               1)
    plt.axline(xy1=(0, b + m * (rangelow - 1)), slope=m, linestyle='--')
    
    plt.boxplot(data)
    plt.xticks(ticks=np.array(range(rangeup-rangelow)) + 1, labels=range(rangelow, rangeup))
    plt.xlabel("bits of prime factors")
    plt.ylabel("runtime seconds (log2-scale)")
    plt.title("Glucose4 vs factoring instances")
    
    plt.savefig('results/figure_1.png', dpi=1000)