# load RSlurmSimTools
library(RSlurmSimTools)

# change working directory to script location
#top_dir <- dirname(rstudioapi::getActiveDocumentContext()$path)
top_dir <- getwd() # gets current directory they are in
setwd(top_dir)

#library(ggplot2)
#library(scales)
#library(lubridate)
#library(stringr)



# This script generate job trace with large number of jobs
# First different types of jobs are specified, followed by random pick from
# this job types banck with random walltime limit and execution walltime



#Big Memory Jobs Template
job_types__bigmem <- list(
    sim_job( #big_mem_job
        tasks = 1L,
        tasks_per_node = 1L,
        req_mem = 500000,
        req_mem_per_cpu = 0L,
        freq = 1/3
    ),
    sim_job(#big_mem_job
        tasks = 6L,
        tasks_per_node = 6L,
        req_mem = 500000,
        req_mem_per_cpu = 0L,
        freq = 1/3
    ),
    sim_job(#big_mem_job
        tasks = 12L,
        tasks_per_node = 12L,
        req_mem = 500000,
        req_mem_per_cpu = 0L,
        freq = 1/3
    )
)

#GPU Jobs Template
job_types__gpu <- list(
    sim_job( #gpu
        tasks = 1L,
        tasks_per_node = 1L,
        gres = "gpu:1",
        freq = 1/3
    ),
    sim_job( #gpu
        tasks = 2L,
        tasks_per_node = 2L,
        gres = "gpu:2",
        freq = 1/3
    ),
    sim_job( #gpu
        tasks = 12L,
        tasks_per_node = 12L,
        gres = "gpu:2",
        freq = 1/3
    )
)
# General compute jobs with variable node count
job_types__gen_comp <- list(
    sim_job( #abitrary serial 1/2 for named resources 8/7 nodes/records * weights
        tasks = 1L,
        tasks_per_node = 1L,
        freq = 0.2
    ),
    sim_job( #abitrary 6 cores
        tasks = 6L,
        tasks_per_node = 6L,
        freq = 0.2
    ),
    sim_job( #abitrary single node
        tasks = 12L,
        tasks_per_node = 12L,
        freq = 0.2
    ),
    sim_job( #abitrary 2 node
        tasks = 24L,
        tasks_per_node = 12L,
        freq = 0.1
    ),
    sim_job( #abitrary 3 node
        tasks = 36L,
        tasks_per_node = 12L,
        freq = 0.1
    ),
    sim_job( #abitrary 4 node
        tasks = 48L,
        tasks_per_node = 12L,
        freq = 0.1
    ),
    sim_job( #abitrary 8 node
        tasks = 96L,
        tasks_per_node = 12L,
        freq = 0.1
    )
)
job_types__gen_comp <- lapply(job_types__gen_comp
                              , function(x){
    x$freq <- 4*x$freq
    x
})

# General compute jobs with variable node count and request for CPU-N
job_types__cpu_n <- list(
    sim_job( #abitrary serial 1/2 for named resources 8/6 nodes/records * weights
        tasks = 1L,
        tasks_per_node = 1L,
        features = "CPU-N",
        freq = 0.3
    ),
    sim_job( #abitrary 6 cores
        tasks = 6L,
        tasks_per_node = 6L,
        features = "CPU-N",
        freq = 0.2
    ),
    sim_job( #abitrary single node
        tasks = 12L,
        tasks_per_node = 12L,
        features = "CPU-N",
        freq = 0.2
    ),
    sim_job( #abitrary 2 node
        tasks = 24L,
        tasks_per_node = 12L,
        features = "CPU-N",
        freq = 0.1
    ),
    sim_job( #abitrary 3 node
        tasks = 36L,
        tasks_per_node = 12L,
        features = "CPU-N",
        freq = 0.1
    ),
    sim_job( #abitrary 4 node
        tasks = 48L,
        tasks_per_node = 12L,
        features = "CPU-N",
        freq = 0.1
    )
)
job_types__cpu_n <- lapply(job_types__cpu_n, function(x){
    x$freq <- 2*x$freq
    x
})
# General compute jobs with variable node count and request for CPU-M
job_types__cpu_m <- list(
    sim_job( #abitrary serial 1/2 for named resources 8/6 nodes/records * weights
        tasks = 1L,
        tasks_per_node = 1L,
        features = "CPU-M",
        freq = 0.3
    ),
    sim_job( #abitrary 6 cores
        tasks = 6L,
        tasks_per_node = 6L,
        features = "CPU-M",
        freq = 0.2
    ),
    sim_job( #abitrary single node
        tasks = 12L,
        tasks_per_node = 12L,
        features = "CPU-M",
        freq = 0.2
    ),
    sim_job( #abitrary 2 node
        tasks = 24L,
        tasks_per_node = 12L,
        features = "CPU-M",
        freq = 0.1
    ),
    sim_job( #abitrary 3 node
        tasks = 36L,
        tasks_per_node = 12L,
        features = "CPU-M",
        freq = 0.1
    ),
    sim_job( #abitrary 4 node
        tasks = 48L,
        tasks_per_node = 12L,
        features = "CPU-M",
        freq = 0.1
    )
)
job_types__cpu_m <- lapply(job_types__cpu_m
                           , function(x){
    x$freq <- 2*x$freq
    x
})


# Make job bank from abave specific job_types
job_types <- c(job_types__bigmem,job_types__gpu
               ,job_types__gen_comp
               ,job_types__cpu_n,job_types__cpu_m
               )

# Normalize freq to prob for job distribution
prob <- sapply(job_types, function(x){x$freq})
prob <- prob / sum(prob)

# Set Number of Jobs
N <- 500

# Seed the seed
set.seed(20170318)

# Generate job trace
r<-sample(job_types, size = N, replace = TRUE, prob = prob)

# Convert to data.frame
trace <- do.call(rbind, lapply(r,data.frame)) 


# Set proper users and accounts
users <- list(
    list("user1","account1"),
    list("user2","account1"),
    list("user3","account1"),
    list("user4","account2"),
    list("user5","account2")
)

ua <- sample(users, size = N, replace = TRUE)
trace$sim_username <- sapply(ua,function(x){x[[1]]})
trace$sim_account <- sapply(ua,function(x){x[[2]]})

# Set walltime limits (in minutes) and duration (in seconds)
true_min <- 5L
true_max <- 30L
wclimit <- as.integer(runif(N,min=true_min-2L,max=true_max+2L))
wclimit[wclimit<true_min] <- true_min
wclimit[wclimit>true_max] <- true_max

duration_factor <- runif(N,min=-0.2,max=1.2)
duration_factor[duration_factor<0.0] <- 0.0
# in original it was set to 1.0
# in current version it will be -1 so slurm should kill them due
# to exceeding timelimit
# duration_factor[duration_factor>1.0] <- 1.0
duration_factor[duration_factor>1.0] <- -1.0

duration <- as.integer(round(duration_factor*wclimit*60.0))
duration[duration<0] <- -1

trace$sim_wclimit <- wclimit
trace$sim_duration <- duration

sum(trace$sim_duration*trace$sim_tasks)/3600.0/120.0

# Set submit time
t0 <- as.POSIXct("2017-01-01 00:00:00")
submit <- as.integer(runif(N,min=0,max=7*3600))+t0

trace$sim_submit <- submit
trace$sim_submit_ts <- as.integer(submit)

# Sort by submit time
trace<-trace[order(trace$sim_submit_ts),]

# Generate job ids
trace$sim_job_id <- 1:N + 1000L

#write old job trace for Slurm Simulator
# write_trace(file.path(top_dir, "reg_testing/micro_cluster/docker/etc", "test.trace"),trace)

#write job trace as csv for reture reference
write.csv(trace, file.path(top_dir, "reg_testing/micro_cluster/docker/etc", "jobs500.csv"))

#new job trace as csv for reture reference

head(trace)
trace$dt <- trace$sim_submit_ts - min(trace$sim_submit_ts)




seconds_to_slurm_duration <- function (seconds) {
    seconds <- as.integer(seconds)
    days <- seconds %/% (24L*3600L)
    hms <- seconds %% (24L*3600L)
    h <- hms %/% 3600L
    ms <- hms %% 3600L
    m <- ms %/% 60L
    s <- ms %% 60L
    if(days > 0L) {
        sprintf("%d-%02d:%02d:%02d",days,h,m,s)
    } else {
        sprintf("%02d:%02d:%02d",h,m,s)
    }

}

get_sim_event <- function (trace) {
    sim_event <- rep.int("",nrow(trace))
    for(i in 1:(nrow(trace))) {
        event <- paste(
            "-dt", trace$dt[i], "-e submit_batch_job |",
            "-jid ", trace$sim_job_id[i],
            "-sim-walltime", trace$sim_duration[i],
            paste0("--uid=", trace$sim_username[i]),
            "-t", seconds_to_slurm_duration(trace$sim_wclimit[i]*60L),
            "-n", trace$sim_tasks[i],
            paste0("--ntasks-per-node=", trace$sim_tasks_per_node[i]),
            "-A", trace$sim_account[i],
            "-p", trace$sim_partition[i],
            "-q", trace$sim_qosname[i]
            )
        if (trace$sim_cpus_per_task[i] != 1L) {
            event <- paste(event, paste0("--cpus-per-task=", trace$sim_tasks_per_node[i]))
        }
        if (trace$sim_cancelled_ts[i] != 0L) {
            error("Job cancelling is not implemented yet")
        }
        if (trace$sim_dependency[i] != "") {
            error("Job dependencies are not implemented yet")
        }
        if (trace$sim_shared[i] == 0) {
            event <- paste(event, "--exclusive")
        }
        if (!is.na(trace$sim_req_mem[i])) {
            if (trace$sim_req_mem_per_cpu[i]) {
                event <- paste(event, paste0("--mem-per-cpu=", trace$sim_req_mem[i]))
            } else {
                event <- paste(event, paste0("--mem=", trace$sim_req_mem[i]))
            }
        }
        if (trace$sim_features[i] != "") {
            event <- paste(event, paste0("--constraint=", trace$sim_features[i]))
        }
        if (trace$sim_gres[i] != "") {
            event <- paste(event, paste0("--gres=", trace$sim_gres[i]))
        }
        event <- paste(event, "pseudo.job")
        sim_event[i] <- event
    }
    sim_event
}
trace$sim_event <- get_sim_event(trace)

write(trace$sim_event, file = file.path(top_dir, "reg_testing/micro_cluster/docker/etc", "jobs500.events"))


trace$dt <- trace$dt %/% 30
trace$sim_wclimit <- trace$sim_wclimit %/% 30
trace$sim_wclimit[trace$sim_wclimit < 1L] <-1L
trace$sim_duration <- trace$sim_duration %/% 30
trace$sim_duration[trace$sim_duration<0] <- -1
trace$sim_event <- get_sim_event(trace)

write(trace$sim_event, file = file.path(top_dir, "reg_testing/micro_cluster/docker/etc", "jobs500_shrinked.events"))

# "",""

#"","sim_job_id","sim_submit","sim_wclimit","sim_duration","sim_tasks","sim_tasks_per_node","sim_username",
# "sim_submit_ts","sim_qosname","sim_partition","sim_account","sim_req_mem","sim_req_mem_per_cpu",
# "sim_features","sim_gres","sim_shared","sim_cpus_per_task","sim_dependency","sim_cancelled_ts","freq"

#"341",1001,2017-01-01 00:01:26,7,15,12,12,"user5",1483246886,"normal","normal","account2",NA,0,"","",1,1,"",0,0.8
