generate-orange:
	python3 -m sample.orange.prepare_instance \
		--link_file=../data/raw/orange/Outputs/Instances/1.5x/efficient/German_17_26/Links/30_demands-b/Link.csv\
		--execution_file=../data/raw/orange/Outputs/executionOutputs/German_17_26/oP_L1.5x_Teff_iGerman_17_26_d30-b_ofNLUS_f0_cd1_os1_gn0_b1_r0_cu0_p2.txt \
		--output_file=../data/instance/German_17_26/orange_german_17_26_d30-b.json \
		--num_failed_links=1

# ==============================================================================================================================================================================

plot-orange-topology:
	python3 main.py \
		--instance_file=../data/instance/German_17_26/orange_german_17_26_d30-b.json \
		--plot_type=topology \
		--figure_file=../data/figure/German_17_26/orange_german_17_26_d30-b_topology.pdf

# ==============================================================================================================================================================================

solve-orange-model:
	mkdir -p ../data/log/German_17_26/
	python3 main.py \
		--instance_file=../data/instance/German_17_26/orange_german_17_26_d30-b.json \
		--plot_type=solve \
		--solution_file=../data/solution/German_17_26/orange_german_17_26_d30-b_solution.json 2>&1 | tee ../data/log/German_17_26/orange_german_17_26_d30-b_gurobi.log

# ==============================================================================================================================================================================

plot-orange-result-by-demand:
	python3 main.py \
		--instance_file=../data/instance/German_17_26/orange_german_17_26_d30-b.json \
		--plot_type=result_by_demand \
		--solution_file=../data/solution/German_17_26/orange_german_17_26_d30-b_solution.json \
		--figure_dir=../data/figure/German_17_26/orange_german_17_26_d30-b_by_demand
