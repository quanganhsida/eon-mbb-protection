generate-orange:
	python3 -m sample.orange.prepare_instance \
		--link_file=../data/raw/orange/Outputs/Instances/1.5x/efficient/Nsfnet_14_21/Links/90_demands-b/Link.csv\
		--execution_file=../data/raw/orange/Outputs/executionOutputs/oP_L1.5x_Teff_iNsfnet_14_21_d90-b_ofNLUS_f0_cd1_os1_gn0_b1_r0_cu0_p2.txt \
		--output_file=../data/instance/Nsfnet_14_21/orange_nsfnet_14_21_d90-b.json \
		--num_failed_links=1

# ==============================================================================================================================================================================

plot-orange-topology:
	python3 main.py \
		--instance_file=../data/instance/Nsfnet_14_21/orange_nsfnet_14_21_d90-b.json \
		--plot_type=topology \
		--figure_file=../data/figure/Nsfnet_14_21/orange_nsfnet_14_21_d90-b_topology.pdf

# ==============================================================================================================================================================================

solve-orange-model:
	mkdir -p ../data/log/Nsfnet_14_21/
	python3 main.py \
		--instance_file=../data/instance/Nsfnet_14_21/orange_nsfnet_14_21_d90-b.json \
		--plot_type=solve \
		--solution_file=../data/solution/Nsfnet_14_21/orange_nsfnet_14_21_d90-b_solution.json 2>&1 | tee ../data/log/Nsfnet_14_21/orange_nsfnet_14_21_d90-b_gurobi.log

# ==============================================================================================================================================================================

plot-orange-result-by-demand:
	python3 main.py \
		--instance_file=../data/instance/Nsfnet_14_21/orange_nsfnet_14_21_d90-b.json \
		--plot_type=result_by_demand \
		--solution_file=../data/solution/Nsfnet_14_21/orange_nsfnet_14_21_d90-b_solution.json \
		--figure_dir=../data/figure/Nsfnet_14_21/orange_nsfnet_14_21_d90-b_by_demand
