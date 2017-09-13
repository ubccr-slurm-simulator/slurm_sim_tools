library(ggplot2)
library(scales)
library(lubridate)
library(stringr)

library(rPython)
library(Rcpp)

top_dir <- "/home/mikola/slurm_simulator3/slurm_sim_tools/validation"

setwd(top_dir)
source("../Rutil/trace_job_util.R")

sdiag<-read.csv("sdiag.csv")

sdiag$sdiag_output_time <- as.POSIXct(sdiag$sdiag_output_time,format = "%Y-%m-%d %H:%M:%S")

sdiag$jobs_pending <- sdiag$jobs_submitted - sdiag$jobs_started - sdiag$jobs_completed -sdiag$jobs_canceled-sdiag$jobs_failed

plot(sdiag$sdiag_output_time, sdiag$jobs_pending)
