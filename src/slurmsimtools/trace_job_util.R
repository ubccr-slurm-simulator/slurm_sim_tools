#library(lubridate)
library(rPython)
library(Rcpp)



#rutil_dir <- normalizePath(dirname(sys.frame(1)$ofile))
rutil_dir <- "."
#rutil_dir <- dirname(rstudioapi::getActiveDocumentContext()$path)
#print(sys.nframe())              
#print(rutil_dir)
#sourceCpp(file.path(rutil_dir,"save_trace.cpp"))
sourceCpp(file.path(rutil_dir,"save_trace.cpp"))

last_job_id <- 1000L
sim_job <- function(job_id = NA,
                    submit = NA,
                    wclimit = 0L,
                    duration = 0L,
                    tasks = 0L,
                    tasks_per_node = 0L,
                    username = "mikola",
                    qosname = "normal",
                    partition = "normal",
                    account = "testacct",
                    req_mem = NA,
                    req_mem_per_cpu = 0L,
                    features = "",
                    gres = "",
                    shared = 1L,
                    cpus_per_task = 1L,
                    dependency = "",
                    cancelled = NA,...){
    if(is.na(submit)){
        #error("submit can not be NA")
        submit <- NA
        submit_ts <- NA
    }else{
        submit <- as.POSIXct(submit)
        submit_ts <- as.integer(submit)
    }
    if(is.na(job_id)){
        job_id <- last_job_id+1L
    }
    job_id <- as.integer(job_id)
    last_job_id <<- job_id
    
    
    wclimit <- as.integer(wclimit)
    duration <- as.integer(duration)
    tasks <- as.integer(tasks)
    tasks_per_node <- as.integer(tasks_per_node)
    req_mem = as.integer(req_mem)
    req_mem_per_cpu <- as.integer(req_mem_per_cpu)
    shared <- as.integer(shared)
    cpus_per_task <- as.integer(cpus_per_task)
    if(is.na(cancelled)){
        cancelled_ts <- 0L
    }else{
        cancelled <- as.POSIXct(cancelled)
        cancelled_ts <- as.integer(cancelled)
    }
    list(
        sim_job_id = job_id,
        sim_submit = submit,
        sim_wclimit = wclimit,
        sim_duration = duration,
        sim_tasks = tasks,
        sim_tasks_per_node = tasks_per_node,
        sim_username = username,
        sim_submit_ts = submit_ts,
        sim_qosname = qosname,
        sim_partition = partition,
        sim_account = account,
        sim_req_mem = req_mem,
        sim_req_mem_per_cpu = req_mem_per_cpu,
        sim_features = features,
        sim_gres = gres,
        sim_shared = shared,
        sim_cpus_per_task = cpus_per_task,
        sim_dependency = dependency,
        sim_cancelled_ts = cancelled_ts,
        ...
    )
}
get_sim <- function(filename,prefix="simed_"){
    jobs_sim <- read.table(filename,header = TRUE, sep = "|")
    jobs_sim$Submit <- as.POSIXct(jobs_sim$Submit,format = "%Y-%m-%dT%H:%M:%S")
    jobs_sim$Start <- as.POSIXct(jobs_sim$Start,format = "%Y-%m-%dT%H:%M:%S")
    jobs_sim$End <- as.POSIXct(jobs_sim$End,format = "%Y-%m-%dT%H:%M:%S")
    jobs_sim$duration <- (unclass(jobs_sim$End) - unclass(jobs_sim$Start))
    
    colnames(jobs_sim)<-paste0(prefix,colnames(jobs_sim))
    
    jobs_sim
}


write_trace <- function(trace_filename,trace){
    #delete trace file if it exists
    if(file.exists(trace_filename))file.remove(trace_filename)
    
    #check that all columns present
    
    #check values
    
    #write trace
    write_trace_cpp(trace_filename,trace)
}

extract_slurm_period <- function(v) {
    #v1 <- sub("^([0-9]{2}):([0-9]{2}):([0-9]{2})","0-\\1:\\2:\\3",t0)
    v2 <- as.integer(str_match(v,"(([0-9])+-)?([0-9]{2}):([0-9]{2}):([0-9]{2})")[,3:6])
    v2 <- matrix(v2,nrow = length(v))
    v2[is.na(v2[,1]),1] <- 0
    
    #sec <- v2[,1]*24*60*60+v2[,2]*60*60+v2[,3]*60+v2[,4]
    
    duration(second = v2[,4], minute = v2[,3], hour = v2[,2], day = v2[,1])
}

python.load(file.path(rutil_dir,"..","src","hostlist.py"))

read_sacct_out <- function(filename,nodes_desc=NULL){
    slurm_log <- read.table(filename, header = TRUE, sep = "|",as.is = TRUE)
    
    #convert to proper format
    for(col in c("Submit","Eligible","Start","End")){
        slurm_log[,col] <- as.POSIXct(slurm_log[,col],format = "%Y-%m-%dT%H:%M:%S")
    }
    
    #duration
    for(col in c("Elapsed","Timelimit")){
        slurm_log[,col] <- extract_slurm_period(slurm_log[,col])
    }
    
    #factor
    for(col in c("Cluster","Partition","Account","Group","User", "ExitCode","State","QOS")){
        slurm_log[,col] <- factor(slurm_log[,col])
    }
    
    #state
    slurm_log$State <- as.character(slurm_log$State)
    slurm_log$State[grepl("CANCELLED",slurm_log$State)] <- "CANCELLED"
    slurm_log$State <- as.factor(slurm_log$State)
    
    colnames(slurm_log)[2] <- "local_job_id"
    
    #extract node list
    python.load(file.path(rutil_dir,"..","src","hostlist.py"))
    #slurm_log$NodeListFull <- python.call("expand_hostlists_to_str",slurm_log$NodeList)
    slurm_log$NodeListFull <- python.call("expand_hostlists_to_list",slurm_log$NodeList)

    #convert memory
    reqmem <- str_match_all(slurm_log$ReqMem, "([\\.0-9]+)([MG])([nc])")
    reqmem_size <- sapply(reqmem,function(r)as.integer(r[[2]]))
    reqmem_unit <- sapply(reqmem,function(r)r[[3]])
    reqmem_perwhat <- sapply(reqmem,function(r)r[[4]])
    #convert to MB
    reqmem_size[reqmem_unit=="G"] <- reqmem_size[reqmem_unit=="G"]*1024
    
    slurm_log$ReqMemSize <- reqmem_size
    slurm_log$ReqMemPerNode <- reqmem_perwhat=="n"
    
    slurm_log$ReqMem <- NULL
    
    #set proper NA
    #slurm_log$ReqGRES[slurm_log$ReqGRES==""] <- NA
    if(!is.null(nodes_desc)){
      nr <- max(sapply(nodes_desc,function(n){length(n$Nodes)}))
      
      nodes_mat <- sapply(nodes_desc,function(n){c(n$Nodes,rep(NA,nr-length(n$Nodes)))})
      
      #assing nodes
      nodes_types_used <- sapply(slurm_log$NodeListFull,function(nodes){
        apply(nodes_mat,2,function(v){length(intersect(v,nodes))})
      })
      
      slurm_log <- cbind(slurm_log,t(nodes_types_used))
    }
    
    slurm_log
}

get_utilization <- function(sacct0,node_desc,dt=60L)
{
    dt <- as.integer(dt)
    
    nodes_names <- unlist(sapply(node_desc,function(x){x$Nodes}))
    total_proc <- sum(unlist(sapply(node_desc,function(x){x$Procs*length(x$Nodes)})))
    
    ts0 <- as.integer(min(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    ts1 <- as.integer(max(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    
    
    ts0 <- as.integer(ts0/dt-1L)*dt
    ts1 <- as.integer(ts1/dt+2L)*dt
    
    ts <- seq(ts0,ts1,dt)
    t <- as.POSIXct(ts, origin="1970-01-01")
    utilization <- data.frame(ts,t,matrix(data=0.0, ncol = length(nodes_names)+2, nrow = length(ts)))
    colnames(utilization) <- c("ts","t",nodes_names,"total","total_norm")
    
    Njobs <- nrow(sacct0)
    for(ijob in 1:Njobs){
        jts_0 <- as.integer(sacct0$Start[[ijob]])
        jts_1 <- as.integer(sacct0$End[[ijob]])
        
        iperiod0 <- as.integer((jts_0-ts0)/dt) + 1L
        iperiod01 <- iperiod0 + 1L
        iperiod10 <- as.integer((jts_1-ts0)/dt) + 1L
        iperiod1 <- iperiod10 + 1L
        
        ppn <- sacct0$NCPUS[[ijob]]/sacct0$NNodes[[ijob]]
        
        if(iperiod10>iperiod01){
            for(node in sacct0$NodeListFull[[ijob]]){
                utilization[[node]][iperiod01:(iperiod10-1L)] <- utilization[[node]][iperiod01:(iperiod10-1L)] + ppn
            }
        }
        
        if(iperiod10> iperiod0)
        {
            #i.e. two ends
            for(node in sacct0$NodeListFull[[ijob]]){
                utilization[[node]][iperiod0] <- utilization[[node]][iperiod0] + ((ts[iperiod01]-jts_0)/dt)*ppn
                utilization[[node]][iperiod10] <- utilization[[node]][iperiod10] + ((jts_1-ts[iperiod10])/dt)*ppn
            }
        }else{
            for(node in sacct0$NodeListFull[[ijob]]){
                utilization[[node]][iperiod0] <- utilization[[node]][iperiod0] + ((jts_1-jts_0)/dt)*ppn
            }
        }
    }
    utilization$total <- rowSums(utilization[,nodes_names])
    utilization$total_norm <- utilization$total /total_proc
    utilization
}

get_utilization2 <- function(sacct0,node_desc,dt=60L)
{
    dt <- as.integer(dt)
    
    #nodes_names <- unlist(sapply(node_desc,function(x){x$Nodes}))
    total_proc <- sum(unlist(sapply(node_desc,function(x){x$Procs*length(x$Nodes)})))
    
    ts0 <- as.integer(min(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    ts1 <- as.integer(max(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    
    
    ts0 <- as.integer(ts0/dt-1L)*dt
    ts1 <- as.integer(ts1/dt+2L)*dt
    
    ts <- seq(ts0,ts1,dt)
    t <- as.POSIXct(ts, origin="1970-01-01")
    utilization <- data.frame(ts,t,matrix(data=0.0, ncol = 2, nrow = length(ts)))
    colnames(utilization) <- c("ts","t","total","total_norm")
    
    Njobs <- nrow(sacct0)
    for(ijob in 1:Njobs){
        jts_0 <- as.integer(sacct0$Start[[ijob]])
        jts_1 <- as.integer(sacct0$End[[ijob]])
        
        iperiod0 <- as.integer((jts_0-ts0)/dt) + 1L
        iperiod01 <- iperiod0 + 1L
        iperiod10 <- as.integer((jts_1-ts0)/dt) + 1L
        iperiod1 <- iperiod10 + 1L
        
        ncpus <- sacct0$NCPUS[[ijob]]
        
        if(iperiod10>iperiod01){
            utilization$total[iperiod01:(iperiod10-1L)] <- utilization$total[iperiod01:(iperiod10-1L)] + ncpus
        }
        
        if(iperiod10> iperiod0)
        {
            #i.e. two ends
            utilization$total[iperiod0] <- utilization$total[iperiod0] + ((ts[iperiod01]-jts_0)/dt)*ncpus
            utilization$total[iperiod10] <- utilization$total[iperiod10] + ((jts_1-ts[iperiod10])/dt)*ncpus
        }else{
            utilization$total[iperiod0] <- utilization$total[iperiod0] + ((jts_1-jts_0)/dt)*ncpus
        }
    }
    utilization$total_norm <- utilization$total /total_proc
    utilization
}

get_utilizationUsingReqCPUS <- function(sacct0,node_desc,dt=60L)
{
    dt <- as.integer(dt)
    
    #nodes_names <- unlist(sapply(node_desc,function(x){x$Nodes}))
    total_proc <- sum(unlist(sapply(node_desc,function(x){x$Procs*length(x$Nodes)})))
    
    ts0 <- as.integer(min(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    ts1 <- as.integer(max(unlist(sacct0[,c("Submit","Eligible","Start","End")]),na.rm = TRUE))
    
    
    ts0 <- as.integer(ts0/dt-1L)*dt
    ts1 <- as.integer(ts1/dt+2L)*dt
    
    ts <- seq(ts0,ts1,dt)
    t <- as.POSIXct(ts, origin="1970-01-01")
    utilization <- data.frame(ts,t,matrix(data=0.0, ncol = 2, nrow = length(ts)))
    colnames(utilization) <- c("ts","t","total","total_norm")
    
    Njobs <- nrow(sacct0)
    for(ijob in 1:Njobs){
        jts_0 <- as.integer(sacct0$Start[[ijob]])
        jts_1 <- as.integer(sacct0$End[[ijob]])
        
        iperiod0 <- as.integer((jts_0-ts0)/dt) + 1L
        iperiod01 <- iperiod0 + 1L
        iperiod10 <- as.integer((jts_1-ts0)/dt) + 1L
        iperiod1 <- iperiod10 + 1L
        
        ncpus <- sacct0$ReqCPUS[[ijob]]
        
        if(iperiod10>iperiod01){
            utilization$total[iperiod01:(iperiod10-1L)] <- utilization$total[iperiod01:(iperiod10-1L)] + ncpus
        }
        
        if(iperiod10> iperiod0)
        {
            #i.e. two ends
            utilization$total[iperiod0] <- utilization$total[iperiod0] + ((ts[iperiod01]-jts_0)/dt)*ncpus
            utilization$total[iperiod10] <- utilization$total[iperiod10] + ((jts_1-ts[iperiod10])/dt)*ncpus
        }else{
            utilization$total[iperiod0] <- utilization$total[iperiod0] + ((jts_1-jts_0)/dt)*ncpus
        }
    }
    utilization$total_norm <- utilization$total /total_proc
    utilization
}
