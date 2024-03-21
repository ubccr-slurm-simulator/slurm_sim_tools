
read_sacct_out <- function(filename,nodes_desc=NULL,extract_node_list=FALSE){
    cat("Read: ",filename,"\n")

    if(grepl(".zst", filename, fixed=TRUE)){
      slurm_log <- data.table::fread(cmd=paste("zstdcat", filename),sep="|",header=TRUE)
    } else {
      slurm_log <- data.table::fread(filename,sep="|",header=TRUE)
    }

    #for(col in c("Submit","Eligible","Start","End","Elapsed","Timelimit",
    #             "Cluster","Partition","Account","Group","User", "ExitCode","State","QOS")){
        #cat(paste0(col,"S=",col,",\n"))
        #cat(paste0(col,"S,"))
    #}
    slurm_log <-  dplyr::rename(slurm_log,
        JobId=JobID,
        JobIdRaw=JobIDRaw,
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
    #convert job names
    slurm_log$JobRecID <- as.integer(str_replace(slurm_log$JobName, "jobid_",""))
    if(sum(is.na(slurm_log$JobRecID)) > 0.5 * length(slurm_log$JobRecID )) {
      slurm_log$JobRecID <- as.integer(str_replace(slurm_log$JobName, "job_",""))
    }
    if(sum(is.na(slurm_log$JobRecID)) > 0.5 * length(slurm_log$JobRecID )) {
      warning("Can not extract job id from job name will use raw job id")
      slurm_log$JobRecID <- slurm_log$JobIdRaw
    }

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
    reqmem <- stringr::str_match_all(slurm_log$ReqMem, "([\\.0-9]+)([MG])([nc]?)")

    reqmem_size <- sapply(reqmem,function(r){
        as.integer(r[[2]])
    })
    reqmem_unit <- sapply(reqmem,function(r)r[[3]])
    reqmem_perwhat <- sapply(reqmem,function(r)r[[4]])
    #convert to MB
    reqmem_size[reqmem_unit=="G"] <- reqmem_size[reqmem_unit=="G"]*1024

    slurm_log$ReqMemSize <- reqmem_size
    slurm_log$ReqMemPerNode <- reqmem_perwhat=="n" | reqmem_perwhat==""

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

    min_time <- min(min(slurm_log$SubmitTS, na.rm=TRUE),min(slurm_log$StartTS, na.rm=TRUE),min(slurm_log$EndTS, na.rm=TRUE), na.rm=TRUE)

    slurm_log$SubmitTime <- slurm_log$SubmitTS - min_time
    slurm_log$StartTime <- slurm_log$StartTS - min_time
    slurm_log$EndTime <- slurm_log$EndTS - min_time
    slurm_log$WallTime <- slurm_log$EndTime - slurm_log$StartTime
    slurm_log$WaitTime <- slurm_log$StartTime - slurm_log$SubmitTime

    slurm_log <- relocate(slurm_log, JobRecID, SubmitTime, StartTime, EndTime, WallTime, WaitTime, .before = "JobId")

    return(slurm_log)
}

read_sacct_out_multiple <- function(slurm_mode, results_root_dir, dtstart_list, run_id_list, sacct_out="slurm_acct.out") {
  result_list <- list()
  for(dtstart in dtstart_list) {
    for(run_id in run_id_list) {
      m_result_root_dir <- path.expand(file.path(results_root_dir, paste0("dtstart_", dtstart, "_", run_id)))
      m_sacct_out_filename <- file.path(m_result_root_dir, sacct_out)

      if(!dir.exists(m_result_root_dir)) {
          warning(sprintf("Directory %s does not exists!", m_result_root_dir))
          return(NULL);
      }
      if(!file.exists(m_sacct_out_filename)) {
          if (file.exists(paste0(m_sacct_out_filename,".zst"))) {
              m_sacct_out_filename <- paste0(m_sacct_out_filename,".zst")
          } else {
              warning(sprintf("File %s does not exists!", m_sacct_out_filename))
              return(NULL);
          }
      }
      m_sacct_out <- read_sacct_out(m_sacct_out_filename)
      m_sacct_out$slurm_mode <- slurm_mode
      m_sacct_out$dtstart <- dtstart
      m_sacct_out$run_id <- run_id

      m_sacct_out <- relocate(m_sacct_out,slurm_mode,dtstart,run_id, .before = "JobRecID")
      result_list[[length(result_list)+1]] <- m_sacct_out

    }
  }
  return(data.table::rbindlist(result_list))
}


read_events_csv <- function(filename,nodes_desc=NULL,extract_node_list=FALSE){
    cat("Read: ",filename,"\n")

    if(grepl(".zst", filename, fixed=TRUE)){
      events <- data.table::fread(cmd=paste("zstdcat", filename),sep=",",header=TRUE)
    } else {
      events <- data.table::fread(filename,sep=",",header=TRUE)
    }

    return(events)
}

read_events_multiple <- function(slurm_mode, results_root_dir, dtstart_list, run_id_list, events_csv="slurmctld_log.csv") {
  result_list <- list()
  for(dtstart in dtstart_list) {
    for(run_id in run_id_list) {
      m_result_root_dir <- path.expand(file.path(results_root_dir, paste0("dtstart_", dtstart, "_", run_id)))
      m_events_csv_filename <- file.path(m_result_root_dir, events_csv)

      if(!dir.exists(m_result_root_dir)) {
          warning(sprintf("Directory %s does not exists!", m_result_root_dir))
          return(NULL);
      }
      if(!file.exists(m_events_csv_filename)) {
          if (file.exists(paste0(m_events_csv_filename,".zst"))) {
              m_events_csv_filename <- paste0(m_events_csv_filename,".zst")
          } else {
              warning(sprintf("File %s does not exists!", m_events_csv_filename))
              return(NULL);
          }
      }
      m_events_csv <- read_events_csv(m_events_csv_filename)
      m_events_csv$slurm_mode <- slurm_mode
      m_events_csv$dtstart <- dtstart
      m_events_csv$run_id <- run_id

      m_events_csv <- relocate(m_events_csv,slurm_mode,dtstart,run_id, .before = "job_rec_id")
      result_list[[length(result_list)+1]] <- m_events_csv

    }
  }
  return(data.table::rbindlist(result_list))
}