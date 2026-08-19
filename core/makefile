generate-orange:
	python3 -m sample.orange.prepare_instance \
		--link_file=../data/raw/orange/Outputs/Instances/1.5x/efficient/European_18_40/Links/30_demands-b/Link.csv\
		--execution_file=../data/raw/orange/Outputs/executionOutputs/oP_L1.5x_Teff_iEuropean_18_40_d30-b_ofNLUS_f0_cd1_os1_gn0_b1_r0_cu0_p2.txt \
		--output_file=../data/instance/european_18_40/orange_european_18_40_d30-b.json \
		--num_failed_links=1

# ==============================================================================================================================================================================

plot-orange-topology:
	python3 main.py \
		--instance_file=../data/instance/european_18_40/orange_european_18_40_d30-b.json \
		--plot_type=topology \
		--figure_file=../data/figure/european_18_40/orange_european_18_40_d30-b_topology.pdf

# ==============================================================================================================================================================================

solve-orange-gurobi:
	mkdir -p ../data/log/european_18_40/
	python3 main.py \
		--instance_file=../data/instance/european_18_40/orange_european_18_40_d30-b.json \
		--plot_type=solve \
		--solution_file=../data/solution/european_18_40/orange_european_18_40_d30-b_solution.json 2>&1 | tee ../data/log/european_18_40/orange_european_18_40_d30-b_solution.log

# ==============================================================================================================================================================================

solve-orange-greedy:
	mkdir -p ../data/log/European_18_40_greedy/
	python3 main.py \
		--instance_file=../data/instance/european_18_40_greedy/orange_european_18_40_d30-b.json \
		--plot_type=solve_greedy \
		--solution_file=../data/solution/European_18_40_greedy/orange_european_18_40_d30-b_greedy_solution.json 2>&1 | tee ../data/log/European_18_40_greedy/orange_european_18_40_d30-b_greedy_solution.log

# ==============================================================================================================================================================================

plot-orange-result-by-demand:
	python3 main.py \
		--instance_file=../data/instance/european_18_40_greedy/orange_european_18_40_d10-b.json \
		--plot_type=result_by_demand \
		--solution_file=../data/solution/European_18_40_greedy/orange_european_18_40_d10-b_greedy_solution.json \
		--figure_dir=../data/figure/european_18_40_greedy/orange_european_18_40_d10-b_greedy_by_demand

# ==============================================================================================================================================================================

compare-orange-solvers:
	mkdir -p ../data/comparison
	python3 -m scenario.compare.compare_solutions \
		--instance_file=../data/instance/european_18_40/orange_european_18_40_d30-b.json \
		--gurobi_solution_file=../data/solution/european_18_40/orange_european_18_40_d30-b_solution.json \
		--greedy_solution_file=../data/solution/European_18_40_greedy/orange_european_18_40_d10-b_greedy_solution.json \
		--output_dir=../data/figure/comparison \
		--case_name=orange_european_18_40_d30-b \


# ==============================================================================================================================================================================

run-comparison-basic: generate-orange plot-orange-topology solve-orange-gurobi solve-orange-greedy compare-orange-solvers
