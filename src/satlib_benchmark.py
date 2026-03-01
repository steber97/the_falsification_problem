import os
import pandas as pd

from factoring.solve_from_file import solve_from_file

benchmark_folder = 'satlib'

if __name__ == "__main__":
    result_df = pd.DataFrame(columns=['name', 'time', 'clauses', 'variables'])
    for f in os.listdir(benchmark_folder):
        result, timer, clauses, variables = solve_from_file("{}/{}".format(benchmark_folder, f))
        result_df.loc[len(result_df)] = [f.replace('.cnf', ''), timer, clauses, variables]
        assert result is True
    result_df.to_csv("results/satlib.csv")