import argparse

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--scenario", type=str, default="main", help="Scenario name to run",)
    parser.add_argument("--instance_file", type=str, default="../data/instance/scenario3.json", help="Path to the instance JSON file.",)
    parser.add_argument("--figure_file", type=str, default="../data/figure/scenario3_topology.pdf", help="Path to save the output figure.",)
    parser.add_argument("--figure_dir", type=str, default="../data/figure/orange", help="Directory to save output figures.",)
    parser.add_argument("--plot_type", type=str, default="topology", choices=["topology", "solution", "solve", "solve_greedy", "result", "result_by_demand"], help="Type of plot to generate.",)
    parser.add_argument("--solution_file", type=str, default="../data/solution/protection/scenario3_basic_solution.json", help="Path to save the optimization solution.",)

    return parser.parse_args()

def get_orange_prepare_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--link_file", required=True, help="Path to Orange Link.csv file.",)
    parser.add_argument("--execution_file", required=True, help="Path to Orange execution output txt file.",)
    parser.add_argument("--output_file", required=True, help="Path to save converted JSON file.",)
    parser.add_argument("--num_failed_links", type=int, default=1, help="Number of failed links to select automatically.",)
    parser.add_argument("--failure_edge_u", type=int, default=None, help="First endpoint of the manually selected failure edge.",)
    parser.add_argument("--failure_edge_v", type=int, default=None, help="Second endpoint of the manually selected failure edge.",)

    return parser.parse_args()
