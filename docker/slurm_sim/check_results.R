#!/usr/bin/env Rscript

# This script gets the results from the simulation and runs some tests on them 
# It tests if the requested features were given to the jobs
# Features: cpu type, gpu, big mem
# How implemented - each feature corresponds to a different type of node


library(RSlurmSimTools) # needs these libraries to run the tests
library(dplyr)

# this function allows easier comparison to see if the simulator assigned things correctly
# checks the trace value (requested feature) against the sacct value (Node List, indicating assigning of a feature)
# the check values are there for reuse of the function for more than one type of test
check_nodes <- function(df.joined, row_num, trace_col, trace_check, sacct_col, sacct_check){
	result = TRUE # assumes correct
	# df.joined is the joined data frame from trace and sacct data frames
	trace_val = df.joined[row_num, trace_col] # trace value (feature)
	sacct_val = df.joined[row_num, sacct_col] # sim value (if implemented feature)
	
	# no feature requested if the value is NA, so check for that
	if(!is.na(trace_val)) 
	{
		# check if the feature (trace_check) was requested
		if(trace_val == trace_check) 
		{
			# checks if the node list has the node corresponding to that feature
			if(!(grepl(sacct_check, sacct_val))) 
			{
				# if improper nodes have been assigned, its a false result (didn't assign properly)
				result = FALSE 
			}
		}
	}
	result # result is returned	
}


# reads in the csv file of the job traces (jobs submitted)
job_trace <- read.csv(file="/home/slurm/slurm_sim_ws/slurm_sim_tools/reg_testing/micro_cluster/test_trace.csv")

# reads in log file of resulting data (what jobs were assigned, where, etc)
sacct_base <- read_sacct_out("/home/slurm/slurm_sim_ws/sim/micro/baseline/results/jobcomp.log")

# creating a joined data frame by job id so that can go through jobs easier
joined <- left_join(job_trace, sacct_base, by = c("sim_job_id" = "local_job_id") )

done_well = TRUE # assumes did correctly

# loops through each row in the joined data frame
for(row in 1:nrow(joined))
{
	# checks if all features have been met (or weren't present)
    done_well = check_nodes(joined, row, "sim_req_mem", 500000, "NodeList", "b") && # big mem
      check_nodes(joined, row, "sim_features", "CPU-M", "NodeList", "m") && # M cpu
      check_nodes(joined, row, "sim_features", "CPU-N", "NodeList", "n") && # N cpu
      check_nodes(joined, row, "sim_gres", "gpu:1", "NodeList", "g") && # 1 gpu
      check_nodes(joined, row, "sim_gres", "gpu:2", "NodeList", "g") # 2 gpu
  	
	# if at any point a feature doesn't match, breaks out of the loop
	if(!done_well) 
	{
		# prints out the job id for tracing back what failed
		jobid = joined[row, "sim_job_id"]
		print(paste("Id of incorrectly assigned job:", jobid))
		break
	}
}
# prints overall result
print("Did the simulator do well?.....")
print(done_well)
