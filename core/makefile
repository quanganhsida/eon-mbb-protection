generate-scenario3:
	python3 -m sample.generate_data

generate-orange:
	python3 -m sample.orange.prepare_instance --link_file=../data/raw/orange/Outputs/Instances/1.5x/efficient/European_18_40/Links/90_demands-b/Link.csv --execution_file=../data/raw/orange/Outputs/executionOutputs/oP_L1.5x_Teff_iEuropean_18_40_d90-b_ofNLUS_f0_cd1_os1_gn0_b1_r0_cu0_p2.txt --output_file=../data/instance/orange/orange_european_18_40_d90_b.json --num_failed_links=1

# ==============================================================================================================================================================================

plot-topology:
	python3 main.py --plot_type=topology --figure_file=../data/figure/scenario3_topology.pdf

plot-orange-topology:
	python3 main.py --instance_file=../data/instance/orange/orange_european_18_40_d90_b.json --plot_type=topology --figure_file=../data/figure/european_18_40/orange_european_18_40_d90_b_topology.pdf

# ==============================================================================================================================================================================

solve-model:
	python3 main.py --plot_type=solve --solution_file=../data/solution/protection/scenario3_basic_solution.json

solve-orange-model:
	python3 main.py --instance_file=../data/instance/orange/orange_european_18_40_d90_b.json --plot_type=solve --solution_file=../data/solution/orange/orange_european_18_40_d90_b_solution.json 2>&1 | tee ../data/log/European_18_40/orange_european_18_40_d90_b_gurobi.log
# ==============================================================================================================================================================================

plot-result:
	python3 main.py --plot_type=result --solution_file=../data/solution/protection/scenario3_basic_solution.json --figure_file=../data/figure/scenario3_model_solution.pdf

plot-orange-result-by-demand:
	python3 main.py --instance_file=../data/instance/orange/orange_european_18_40_d90_b.json --plot_type=result_by_demand --solution_file=../data/solution/orange/orange_european_18_40_d90_b_solution.json --figure_dir=../data/figure/european_18_40/orange_european_18_40_d90_b_by_demand
