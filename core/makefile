generate-orange:
	python3 -m sample.orange.prepare_instance \
		--link_file=../data/raw/orange/Outputs/Instances/1.5x/efficient/European_18_40/Links/70_demands-b/Link.csv\
		--execution_file=../data/raw/orange/Outputs/executionOutputs/oP_L1.5x_Teff_iEuropean_18_40_d70-b_ofNLUS_f0_cd1_os1_gn0_b1_r0_cu0_p2.txt \
		--output_file=../data/instance/European_18_40_z2/orange_european_18_40_d70-b_z2.json \
		--num_failed_links=2

# ==============================================================================================================================================================================

plot-orange-topology:
	python3 main.py \
		--instance_file=../data/instance/European_18_40_z2/orange_european_18_40_d70-b_z2.json \
		--plot_type=topology \
		--figure_file=../data/figure/european_18_40_z2/orange_european_18_40_d70-b_z2_topology.pdf

# ==============================================================================================================================================================================

solve-orange-model:
	mkdir -p ../data/log/European_18_40_z2/
	python3 main.py \
		--instance_file=../data/instance/European_18_40_z2/orange_european_18_40_d70-b_z2.json \
		--plot_type=solve \
		--solution_file=../data/solution/European_18_40_z2/orange_european_18_40_d70-b_z2_solution.json 2>&1 | tee ../data/log/European_18_40_z2/orange_european_18_40_d70-b_z2_gurobi.log

# ==============================================================================================================================================================================

plot-orange-result-by-demand:
	python3 main.py \
		--instance_file=../data/instance/European_18_40_z2/orange_european_18_40_d70-b_z2.json \
		--plot_type=result_by_demand \
		--solution_file=../data/solution/European_18_40_z2/orange_european_18_40_d70-b_z2_solution.json \
		--figure_dir=../data/figure/european_18_40_z2/orange_european_18_40_d70-b_z2_by_demand
