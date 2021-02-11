# load RSlurmSimTools
library(RSlurmSimTools)


# change working directory to this script directory
top_dir <- tryCatch(
    dirname(sys.frame(1)$ofile),
    error=function(cond) {return(dirname(rstudioapi::getActiveDocumentContext()$path))})
print(top_dir)
setwd(top_dir)

#write job trace file using data.frame directly
trace <- data.frame(
    sim_job_id = c(1001L,1002L,1003L),
    sim_username = c("user1","user2","user3"),
    sim_tasks = c(1L,2L,3L),
    sim_cpus_per_task = c(1L,1L,1L),
    sim_tasks_per_node = c(12L,12L,12L),
    sim_submit_ts = c(1483232461L,1483232561L,1483232571L),
    sim_duration = c(60L,30L,40L),
    sim_wclimit = c(300L,100L,200L),
    sim_qosname = c("normal","normal","normal"),
    sim_partition = c("normal","normal","normal"),
    sim_account = c("account1","account1","account1"),
    sim_dependency = c("","",""),
    sim_req_mem = as.integer(c(NA,NA,NA)),
    sim_req_mem_per_cpu = c(0L,0L,0L),
    sim_features = c("","",""),
    sim_gres = c("","",""),
    sim_shared = c(0L,0L,0L),
    sim_cancelled_ts = c(0L,0L,0L)
)
write_trace(file.path(top_dir,"test0.trace"),trace)

#dependency check
trace <- list(
    sim_job(
        job_id=1001,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    ),sim_job(
        job_id=1002,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        dependency="afterok:1001"
    ),sim_job(
        job_id=1003,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    ),sim_job(
        job_id=1004,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        dependency="afterok:1002:1003"
    ),sim_job(
        job_id=1005,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=24L,
        tasks_per_node=12L,
        dependency="afterok:1004"
    )
)
#convert list of lists to data.frame
trace <- do.call(rbind, lapply(trace,data.frame))


write_trace(file.path(top_dir,"dependency_test.trace"),trace)

trace$sim_dependency<-""
write_trace(file.path(top_dir,"dependency_test_nodep.trace"),trace)


#features
trace <- list(
    sim_job(
        job_id=1001,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        features="IB&CPU-M"
    ),sim_job(
        job_id=1002,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        features="IB&CPU-M"
    ),sim_job(
        job_id=1003,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        features="IB&CPU-M"
    ),sim_job(
        job_id=1004,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        features="CPU-M"
    ),sim_job(
        job_id=1005,
        submit="2016-10-01 00:11:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    )
)
#convert list of lists to data.frame
trace <- do.call(rbind, lapply(trace,data.frame))

write_trace(file.path(top_dir,"features_test.trace"),trace)

#gres
trace <- list(
    sim_job(
        job_id=1001,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    ),sim_job(
        job_id=1002,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    ),sim_job(
        job_id=1003,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    ),sim_job(
        job_id=1004,
        submit="2016-10-01 00:01:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L,
        gres = "gpu:2"
    ),sim_job(
        job_id=1005,
        submit="2016-10-01 00:11:00",
        wclimit=300L,
        duration=600L,
        tasks=12L,
        tasks_per_node=12L
    )
)

#convert list of lists to data.frame
trace <- do.call(rbind, lapply(trace,data.frame))

write_trace(file.path(top_dir,"gres_test.trace"),trace)
