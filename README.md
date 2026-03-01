# the_falsification_problem
Repository used in order to produce the experiments in Appendix F of the paper "The falsification problem: how hard is it to falsify heuristics?", submitted at ISCO 2026.

## Install dependencies

Create a virtualenv, and install the requirements with:

```
pip install -r requirements.txt
```

# Reproduce Figure 1 and Table 2

Make sure you are in the `src` folder; in case you are not, just `cd src` into it.

```
python figure_1_table_2.py
```

Results are stored in the folder `src/results`:
- `figure_1.png` is the boxplot in Figure 1.
- `table_2.csv` contains the data for Table 2.

Data and figures might differ slightly from the figure and the table in the paper, because running times depend on the CPU specifications of the machine the experiments have been executed on (MacBook Pro M2).

# Reproduce Table 1 (Satlib benchmark)

Make sure you are in the folder `src`. In case you are not, just `cd src` into it.

```
python table_1.py
```

Results are stored in the folder `results`:
- 'table_1.csv' contains the data for Table 1.
