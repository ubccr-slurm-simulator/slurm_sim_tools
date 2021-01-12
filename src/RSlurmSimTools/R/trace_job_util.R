

#commands to reinstal and reload
# detach("package:RSlurmSimTools", unload=TRUE)
# devtools::document("/home/slurm/slurm_sim_ws/slurm_sim_tools/src/RSlurmSimTools")
# install.packages("/home/slurm/slurm_sim_ws/slurm_sim_tools/src/RSlurmSimTools", repos = NULL, type="source")
# library(RSlurmSimTools)

last_job_id <- 1000L

.onLoad <- function(libname, pkgname) {
    last_job_id <- 1000L
    #print("Hello")
    #print(system.file("python", package = "RSlurmSimTools") )
    #reticulate::source_python("/home/nikolays/slurm_sim_ws/slurm_sim_tools/src/RSlurmSimTools/inst/python/hostlist.py")
    reticulate::source_python(file.path(system.file("python", package = "RSlurmSimTools"),"hostlist.py"))
    #rPython::python.load(file.path(system.file("python", package = "RSlurmSimTools"),"hostlist.py"))
    
    invisible()
}

#' sim_job - Generates R-list with Resource Requested by Job
#' 
#' Generates batch job request details as a list with named members.
#' All arguments have \emph{Default} vaalues. Several outputs from this function
#' can be combined together to data.frame to be fead to \code{\link{write_trace}}
#' 
#' @param job_id Job ID. If it is not set then will use increamented \code{last_job_id values}. \emph{\emph{Default}}: NA
#' @param submit  Date-Time to sumbit job. \emph{Default}: "2001-01-01 00:00:00"
#' @param wclimit  Requested time in minutes. \emph{Default}: 0L
#' @param duration  Simulated actual job walltime in seconds. \emph{Default}: 0L
#' @param tasks  Requested number of tasks. \emph{Default}: 0L
#' @param tasks_per_node  Requested number of tasks per node. \emph{Default}: 0L
#' @param username User name. \emph{Default}: "user1"
#' @param qosname  QoS. \emph{Default}: "normal"
#' @param partition Partition. \emph{Default}: "normal"
#' @param account Account. \emph{Default}: "account1"
#' @param req_mem Requested memory in MiB. \emph{Default}: NA
#' @param req_mem_per_cpu Memory per what? 1L - memory per CPU, 0L - memory per whole job. \emph{Default}: 0L
#' @param features Requested features, a.k.a. constrains. \emph{Default}: ""
#' @param gres General Resources. \emph{Default}: "". Example: "gpu:2"
#' @param shared Is job run in shared mode. \emph{Default}: 1L
#' @param cpus_per_task CPUs per tast. \emph{Default}: 1L
#' @param dependency Dependencies on other jobs. \emph{Default}: "". Example: "afterok:1002:1003"
#' @param cancelled Date-Time to cancel job, if NA job would not be cancelled. \emph{Default}: NA
#' @param ... Other arguments will be appended to returning list
#' @return List with job's requested resources
#'
#' @examples
#' # Generate small job trace file
#' # job trace as list of lists
#' trace <- list(
#'     sim_job(
#'         job_id=1001,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         features="IB&CPU-M"
#'     ),sim_job(
#'         job_id=1002,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         dependency="afterok:1001"
#'     ),sim_job(
#'         job_id=1003,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         gres = "gpu:2"
#'     )
#' )
#' # convert list of lists to data.frame
#' trace <- do.call(rbind, lapply(trace,data.frame))
#' # write job trace
#' write_trace("test.trace",trace)
#' 
sim_job <- function(job_id = NA,
                    submit = "2001-01-01 00:00:00",
                    wclimit = 0L,
                    duration = 0L,
                    tasks = 0L,
                    tasks_per_node = 0L,
                    username = "user1",
                    qosname = "normal",
                    partition = "normal",
                    account = "account1",
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
    last_job_id <- job_id
    
    
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

#' Write Trace Jobs File for Simulation
#' 
#' Write Trace Jobs File for Simulation.
#' 
#' @param trace_filename filename for written trace job file
#' @param trace data.frame with requsted resource
#' 
#' @seealso \code{\link{sim_job}}
#' 
#' @examples
#' # Generate small job trace file
#' # job trace as list of lists
#' trace <- list(
#'     sim_job(
#'         job_id=1001,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         features="IB&CPU-M"
#'     ),sim_job(
#'         job_id=1002,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         dependency="afterok:1001"
#'     ),sim_job(
#'         job_id=1003,
#'         submit="2016-10-01 00:01:00",
#'         wclimit=300L,
#'         duration=600L,
#'         tasks=12L,
#'         tasks_per_node=12L,
#'         gres = "gpu:2"
#'     )
#' )
#' # convert list of lists to data.frame
#' trace <- do.call(rbind, lapply(trace,data.frame))
#' # write job trace
#' write_trace("test.trace",trace)
#' 
write_trace <- function(trace_filename,trace){
    #delete trace file if it exists
    if(file.exists(trace_filename))file.remove(trace_filename)
    
    #check that all columns present and have proper type and values
    errors_count <- 0L
    error_msg <- c("\n")
    
    colprop <- list(
        sim_job_id=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_username=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_tasks=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_cpus_per_task=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_tasks_per_node=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_submit_ts=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_duration=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_wclimit=list(
            col_type="integer",
            na_ok=FALSE
        ),
        sim_qosname=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_partition=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_account=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_dependency=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_req_mem=list(
            col_type="integer",
            na_ok=TRUE
        ),
        sim_req_mem_per_cpu=list(
            col_type="integer",
            na_ok=TRUE
        ),
        sim_features=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_gres=list(
            col_type="character",
            na_ok=FALSE
        ),
        sim_shared=list(
            col_type="integer",
            na_ok=TRUE
        ),
        sim_cancelled_ts=list(
            col_type="integer",
            na_ok=FALSE
        )
    )
    for(col in names(colprop)){
        cat(paste0(col," = c()\n"))
    }
    for(col in names(colprop)){
        #is column in data.frame
        if(!(col %in% colnames(trace))){
            errors_count <- errors_count + 1L
            error_msg <- append(error_msg, paste0(
                "Error #",errors_count, ". Column ",col," is not present in trace data.frame.\n"))
            next
        }
        #is it proper type
        if(typeof(trace[,col])!=colprop[[col]]$col_type){
            if(colprop[[col]]$col_type=="character"){
                if(!is.factor(trace[,col])){
                    errors_count <- errors_count + 1L
                    error_msg <- append(error_msg,paste0(
                        "Error #",errors_count, 
                        ". Column ",col," should be of type ",colprop[[col]]$col_type,
                        " or factor but not ",typeof(trace[,col]),".\n"))
                    next
                }

            } else {
                errors_count <- errors_count + 1L
                error_msg <- append(error_msg,paste0(
                    "Error #",errors_count, 
                    ". Column ",col," should be of type ",colprop[[col]]$col_type,
                    " not ",typeof(trace[,col]),".\n"))
                next
            }
        }
        #is values ok
        if(sum(is.na(trace[,col]))>0L && colprop[[col]]$na_ok==FALSE){
            errors_count <- errors_count + 1L
            error_msg <- append(error_msg,paste0(
                "Error #",errors_count, 
                ". Column ",col," have NA values, but it shouldn't.\n"))
            next
        }
    }
    if(errors_count > 0L){
        stop(error_msg)
    }
    #sort trace
    trace <- dplyr::arrange(trace,sim_submit_ts)
    #write trace
    write_trace_cpp(trace_filename,trace)
    
    invisible()
}

expand_slurm_hostlists <- function(node_list, as_list=TRUE) {
    node_list_expended <- expand_hostlists_to_list(node_list)
    if(as_list) {
        node_list_expended
    } else {
        sapply(jobscomp$node_list_full, FUN=function(x){paste(x,collapse = ',')})
    }
}

extract_slurm_period <- function(v) {
    #v1 <- sub("^([0-9]{2}):([0-9]{2}):([0-9]{2})","0-\\1:\\2:\\3",t0)
    v2 <- as.integer(stringr::str_match(v,"(([0-9])+-)?([0-9]{2}):([0-9]{2}):([0-9]{2})")[,3:6])
    v2 <- matrix(v2,nrow = length(v))
    v2[is.na(v2[,1]),1] <- 0
    
    #sec <- v2[,1]*24*60*60+v2[,2]*60*60+v2[,3]*60+v2[,4]
    
    lubridate::duration(second = v2[,4], minute = v2[,3], hour = v2[,2], day = v2[,1])
}



read_sacct_out <- function(filename,nodes_desc=NULL,extract_node_list=FALSE){
    #slurm_log <- read.table(filename, header = TRUE, sep = "|",as.is = TRUE)
    slurm_log <- data.table::fread(filename,sep="|",header=TRUE)
    
    #for(col in c("Submit","Eligible","Start","End","Elapsed","Timelimit",
    #             "Cluster","Partition","Account","Group","User", "ExitCode","State","QOS")){
        #cat(paste0(col,"S=",col,",\n"))
        #cat(paste0(col,"S,"))
    #}
    slurm_log <-  dplyr::rename(slurm_log,
        JobId=JobID,
        local_job_id=JobIDRaw,
        NodeCount=NNodes,
        SubmitS=Submit,
        EligibleS=Eligible,
        StartS=Start,
        EndS=End,
        ElapsedS=Elapsed,
        TimelimitS=Timelimit,
        ClusterS=Cluster,
        PartitionS=Partition,
        AccountS=Account,
        GroupS=Group,
        UserS=User,
        ExitCodeS=ExitCode,
        StateS=State,
        QOSS=QOS
    )
    
    #convert to proper format
    for(col in c("Submit","Eligible","Start","End")){
        slurm_log[[col]] <- as.POSIXct(slurm_log[[paste0(col,"S")]],format = "%Y-%m-%dT%H:%M:%S")
    }
    
    #duration
    for(col in c("Elapsed","Timelimit")){
        slurm_log[,col] <- extract_slurm_period(slurm_log[[paste0(col,"S")]])
    }
    
    #factor
    for(col in c("Cluster","Partition","Account","Group","User", "ExitCode","State","QOS")){
        slurm_log[,col] <- factor(slurm_log[[paste0(col,"S")]])
    }
    
    #state
    slurm_log$StateS <- as.character(slurm_log$StateS)
    slurm_log$StateS[grepl("CANCELLED",slurm_log$StateS)] <- "CANCELLED"
    slurm_log$State <- as.factor(slurm_log$StateS)
    
    #extract node list
    if(extract_node_list==TRUE){
        #python.load(file.path(rutil_dir,"..","src","hostlist.py"))
        #slurm_log$NodeListFull <- python.call("expand_hostlists_to_str",slurm_log$NodeList)
        slurm_log$NodeListFull <- expand_hostlists_to_list(slurm_log$NodeList)
    }

    #convert memory
    slurm_log$ReqMem[slurm_log$ReqMem=="0n"] <- "0Mn"
    reqmem <- stringr::str_match_all(slurm_log$ReqMem, "([\\.0-9]+)([MG])([nc])")
    
    reqmem_size <- sapply(reqmem,function(r){
        as.integer(r[[2]])
    })
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
    
    slurm_log$SubmitTS <- as.integer(slurm_log$Submit)
    slurm_log$StartTS <- as.integer(slurm_log$Start)
    slurm_log$EndTS <- as.integer(slurm_log$End)
    
    
    slurm_log$WaitHours <- as.integer(slurm_log$Start-slurm_log$Submit)/3600.0
    slurm_log$WaitHours[slurm_log$WaitHours<0.0] <- slurm_log$WaitHours[slurm_log$WaitHours<0.0]+1
    
    slurm_log$WallHours <- as.integer(slurm_log$Elapsed)/3600.0
    slurm_log$NodeHours <- slurm_log$WallHours*slurm_log$NodeCount
    
    #shift 0 value for log scales
    slurm_log$WaitHours4log <- slurm_log$WaitHours
    slurm_log$WaitHours4log[slurm_log$WaitHours4log<1/60]<-1/60
    #shift 0 value for log scales
    slurm_log$WallHours4log <- slurm_log$WallHours
    slurm_log$WallHours4log[slurm_log$WallHours4log<1/60]<-1/60
    
    slurm_log <- dplyr::arrange(slurm_log,SubmitTS)%>%
        dplyr::select(-c(SubmitS,EligibleS,StartS,EndS,ElapsedS,TimelimitS,ClusterS,
                         PartitionS,AccountS,GroupS,UserS,ExitCodeS,StateS,QOSS))
    return(slurm_log)
}

read_perf_stat <- function(filename, tz="GMT") {
    perf_stat <- fromJSON(file = filename)
    for(element in c("slurmdbd_create_time", "slurmd_create_time", "slurmctld_create_time", "jobs_starts")) {
        if(element %in% names(perf_stat) & !is.null(perf_stat[[element]])) {
            perf_stat[[element]] <- as.POSIXct(perf_stat[[element]], origin="1970-01-01", tz="GMT")
            if(tz!="GMT") {
                perf_stat[[element]] <- with_tz(perf_stat[[element]], tz)
            }
        } else {
            perf_stat[[element]] <- NA
        }
    }
    perf_stat
}

read_jobcomp_log <- function(filename, extract_node_list=FALSE, tz="GMT", init_time=NA) {
    # read jobcomp.log file
    con <- file(filename,"r")
    lines <- readLines(con)
    close(con)
    rm(con)

    jobcomp <- data.frame(job_id=rep.int(NA,length(lines)))

    # JobId=1001
    jobcomp$job_id <- as.integer(str_match(lines, "JobId=(\\S+)")[,2])
    # Name=jobid_1001
    jobcomp$ref_job_id <- as.integer(str_match(lines, "Name=jobid_(\\S+)")[,2])
    # UserId=user5(1005)
    tmp <- str_match(lines, "UserId=([A-Za-z0-9]+)\\(([0-9]+)\\)")
    jobcomp$user <- tmp[,2]
    jobcomp$user_id <- as.integer(tmp[,3])
    # GroupId=user5(1005)
    tmp <- str_match(lines, "GroupId=([A-Za-z0-9]+)\\(([0-9]+)\\)")
    jobcomp$group <- tmp[,2]
    jobcomp$group_id <- as.integer(tmp[,3])
    # JobState=COMPLETED
    jobcomp$job_state <- str_match(lines, "JobState=(\\S+)")[,2]
    # Partition=normal
    jobcomp$partition <- str_match(lines, "Partition=(\\S+)")[,2]
    # TimeLimit=1
    jobcomp$time_limit <- str_match(lines, "TimeLimit=(\\S+)")[,2]

    # SubmitTime=2021-01-07T18:19:14
    jobcomp$submit_time <- str_match(lines, "SubmitTime=(\\S+)")[,2]
    # EligibleTime=2021-01-07T18:19:14
    jobcomp$eligible_time <- str_match(lines, "EligibleTime=(\\S+)")[,2]
    # StartTime=2021-01-07T18:19:14
    jobcomp$start_time <- str_match(lines, "StartTime=(\\S+)")[,2]
    # EndTime=2021-01-07T18:19:14
    jobcomp$end_time <- str_match(lines, "EndTime=(\\S+)")[,2]

    # NodeList=b1
    jobcomp$node_list <- str_match(lines, "NodeList=(\\S+)")[,2]
    # NodeCnt=1
    jobcomp$nodes <- as.integer(str_match(lines, "NodeCnt=(\\S+)")[,2])
    # ProcCnt=12
    jobcomp$cpus <- as.integer(str_match(lines, "ProcCnt=(\\S+)")[,2])
    # WorkDir=/home/user5
    jobcomp$work_dir <- str_match(lines, "WorkDir=(\\S+)")[,2]
    # ReservationName=
    jobcomp$reservation_name <- str_match(lines, "ReservationName=(\\S*)")[,2]
    # Gres=
    jobcomp$gres <- str_match(lines, "Gres=(\\S*)")[,2]
    # Account=account2
    jobcomp$account <- str_match(lines, "Account=(\\S+)")[,2]
    # QOS=normal
    jobcomp$qos <- str_match(lines, "QOS=(\\S+)")[,2]
    # WcKey=
    jobcomp$wc_key <- str_match(lines, "WcKey=(\\S*)")[,2]
    # Cluster=micro
    jobcomp$cluster <- str_match(lines, "Cluster=(\\S+)")[,2]

    # DerivedExitCode=0:0
    jobcomp$derived_exit_code <- str_match(lines, "DerivedExitCode=(\\S+)")[,2]
    # ExitCode=0:0
    jobcomp$exit_code <- str_match(lines, "ExitCode=(\\S+)")[,2]

    rm(tmp, lines)

    #convert to proper format
    for(col in c("submit_time","eligible_time","start_time","end_time")){
        #jobcomp[[paste0(col,"S")]] <- jobcomp[[col]]
        jobcomp[[col]] <- as.POSIXct(jobcomp[[col]],format = "%Y-%m-%dT%H:%M:%S", tz="GMT")
        if(tz!="GMT") {
            jobcomp[[col]] <- with_tz(jobcomp[[col]], tz)
        }
    }

    if(!is.na(init_time)) {
        for(col in c("submit_time","eligible_time","start_time","end_time")){
            col_t <- paste0("t_", str_replace(col,"_time",""))
            jobcomp[[col_t]] <- jobcomp[[col]] - init_time
        }
    }

    if(extract_node_list==TRUE){
        jobcomp$node_list_full <- expand_hostlists_to_list(jobcomp$node_list)
    }

    jobcomp$walltime <- jobcomp$end_time - jobcomp$start_time
    jobcomp$waittime <- jobcomp$start_time - jobcomp$submit_time

    jobcomp
}

get_utilization_old <- function(sacct0,node_desc,dt=60L)
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


#' get_utilization - calculate resource utilization
#' 
#' Calculate resource utilization
#' 
#' @param sacct0 data frame with jobs execution history
#' @param total_proc  total number of cores in the resource
#' @param dt  time aggregation size, seconds. \emph{Default}: 60L
#' @return data frame with resource utilization over time
#'
#' @examples
#' 
get_utilization <- function(sacct0,total_proc,dt=60L)
{
    dt <- as.integer(dt)
    total_proc <- as.integer(total_proc)
    
    
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

#' read_simstat_backfill - read backfill execution stats
#' 
#' Cread stats of backfill execution during simulated Slurm Run
#' 
#' @param filename name of file to read
#' @return data frame with resource utilization over time
#'
#' @examples
#' 
read_simstat_backfill <- function(filename)
{
    bf_s <- read.csv(filename)
    colnames(bf_s)[colnames(bf_s) == 'output_time'] <- 't'
    for(col in c("t","last_cycle_when"))bf_s[,col] <- as.POSIXct(bf_s[,col],format = "%Y-%m-%d %H:%M:%S")
    #drop duplicates
    bf_s<-bf_s[bf_s$last_cycle_when>as.POSIXct("2001-01-01"),]
    bf_s<-bf_s[!duplicated(bf_s$last_cycle_when),]
    bf_s$t <- bf_s$last_cycle_when
    bf_s$run_sim_time <- bf_s$last_cycle/1000000.0
    
    return(bf_s)
}
