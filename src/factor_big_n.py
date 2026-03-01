from sympy import isprime
import time

from factoring.factoring_circuit import FactoringCircuit


if __name__ == "__main__":
    # TODO: add factorization!
    # This is the product of {} {} 
    g = 2313177834509145607
    c = FactoringCircuit(g)
    
    cnf, map = c.toCNF()

    # Solve the FactoringCircuit with Glucose4
    cnf_g = cnf.to_glucose()
    print("n={}, clauses={}, literals={}".format(g, len(cnf.clauses), cnf_g.nof_vars()))
    now = time.time()
    solve = cnf_g.solve(assumptions=[map[c.get_output_gate().id]]) 
    total_time = time.time() - now
    print("Total time: {}".format(total_time))
    
    assert solve is True # The multiplication circuit is satisfiable by construction.
    assert solve != isprime(g)  # The number g is not prime by construction.
    
    if solve:
        # Check that, indeed, the certificate for the model encodes the two
        # prime factors a and b.
        model = cnf_g.get_model()
        assert isinstance(model, list)
        f1, f2 = c.getFactorsFromCnfAssignment(model, map)
        assert f1 * f2 == g
        print("The two factors are: ", f1, f2)
