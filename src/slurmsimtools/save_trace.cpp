#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <ctype.h>

#include <Rcpp.h>
using namespace Rcpp;


#define NO_VAL       (0xfffffffe)
#define NO_VAL64   (0xfffffffffffffffe)
#define MEM_PER_CPU  0x8000000000000000
#define OLD_MEM_PER_CPU  0x80000000

typedef struct job_trace {
    int  job_id;
    char *username;
    long int submit; /* relative or absolute? */
    int  duration;
    int  wclimit;
    int  tasks;
    char *qosname;
    char *partition;
    char *account;
    int  cpus_per_task;
    int  tasks_per_node;
    char *reservation;
    char *dependency;
    uint64_t pn_min_memory;/* minimum real memory (in MB) per node OR
     * real memory per CPU | MEM_PER_CPU,
     * NO_VAL use partition default,
     * default=0 (no limit) */
    char *features;
    char *gres;
    int shared;/* 2 if the job can only share nodes with other
     *   jobs owned by that user,
     * 1 if job can share nodes with other jobs,
     * 0 if job needs exclusive access to the node,
     * or NO_VAL to accept the system default.
     * SHARED_FORCE to eliminate user control. */
    long int cancelled; /* time when job should be cancelled, 0 if never */
    struct job_trace *next;
} job_trace_t;

#define write_single_var(v,f) fwrite(&v,sizeof(v),1,f);

int write_string(char *s, FILE *trace_file)
{
    int l=strlen(s);
    fwrite(&l,sizeof(l),1,trace_file);
    if(l>0)fwrite(s,sizeof(char),l,trace_file);
    return 0;
}

int write_single_trace(FILE *trace_file, job_trace_t *trace)
{
    write_single_var(trace->job_id,trace_file);
    write_string(trace->username, trace_file);
    
    write_single_var(trace->submit,trace_file);
    write_single_var(trace->duration,trace_file);
    write_single_var(trace->wclimit,trace_file);
    write_single_var(trace->tasks,trace_file);
    write_string(trace->qosname, trace_file);
    write_string(trace->partition, trace_file);
    write_string(trace->account, trace_file);
    write_single_var(trace->cpus_per_task,trace_file);
    write_single_var(trace->tasks_per_node,trace_file);
    write_string(trace->reservation, trace_file);
    write_string(trace->dependency, trace_file);
    write_single_var(trace->pn_min_memory,trace_file);
    write_string(trace->features, trace_file);
    write_string(trace->gres, trace_file);
    write_single_var(trace->shared,trace_file);
    write_single_var(trace->cancelled, trace_file);
    //  struct job_trace *next;
   return 0;     
}

// [[Rcpp::export]]
void write_trace_cpp(const char * filename, DataFrame jobs) {
    int n=jobs.nrows();
    printf("Writing %d jobs to %s\n",n,filename);
    if(TYPEOF(jobs["sim_job_id"])!=INTSXP)
        stop("sim_job_id should be integer");
    IntegerVector job_id=jobs["sim_job_id"];
    CharacterVector username=jobs["sim_username"];
    
    IntegerVector tasks=jobs["sim_tasks"];
    IntegerVector cpus_per_task=jobs["sim_cpus_per_task"];
    IntegerVector tasks_per_node=jobs["sim_tasks_per_node"];
    
    IntegerVector submit=jobs["sim_submit_ts"];
    IntegerVector duration=jobs["sim_duration"];
    IntegerVector wclimit=jobs["sim_wclimit"];
    
    CharacterVector qosname=jobs["sim_qosname"];
    CharacterVector partition=jobs["sim_partition"];
    CharacterVector account=jobs["sim_account"];
    CharacterVector dependency=jobs["sim_dependency"];
    
    IntegerVector req_mem=jobs["sim_req_mem"];
    IntegerVector req_mem_per_cpu=jobs["sim_req_mem_per_cpu"];
    
    CharacterVector features=jobs["sim_features"];
    CharacterVector gres=jobs["sim_gres"];
    IntegerVector shared=jobs["sim_shared"];
    
    IntegerVector cancelled=jobs["sim_cancelled_ts"];
    
    job_trace_t new_trace;
    
    new_trace.username=(char*)calloc(1024,sizeof(char));
    new_trace.qosname=(char*)calloc(1024,sizeof(char));
    new_trace.partition=(char*)calloc(1024,sizeof(char));
    new_trace.account=(char*)calloc(1024,sizeof(char));
    new_trace.reservation=(char*)calloc(1024,sizeof(char));
    new_trace.dependency=(char*)calloc(10240,sizeof(char));
    new_trace.features=(char*)calloc(1024,sizeof(char));
    new_trace.gres=(char*)calloc(1024,sizeof(char));
    
    FILE *trace_file=NULL;
    //int written;
    if ((trace_file = fopen(filename, "wb")) == NULL) {
        printf("Error opening trace file %s\n", filename);
        return;
    }
    
    for(int i=0;i<n;++i){
        new_trace.job_id = job_id[i];
        strcpy(new_trace.username, as<const char*>(username[i]));
        new_trace.submit=submit[i]; /* relative or absolute? */
        new_trace.duration=duration[i];
        new_trace.wclimit=wclimit[i];
        
        new_trace.tasks=tasks[i];
        new_trace.cpus_per_task=cpus_per_task[i];
        new_trace.tasks_per_node=tasks_per_node[i];
        strcpy(new_trace.qosname, as<const char*>(qosname[i]));
        strcpy(new_trace.partition, as<const char*>(partition[i]));
        strcpy(new_trace.account, as<const char*>(account[i]));
        strcpy(new_trace.dependency, as<const char*>(dependency[i]));

        strcpy(new_trace.reservation, "\0");
        
        if(req_mem[i]==NA_INTEGER){
            new_trace.pn_min_memory=NO_VAL64;
        }else{
            new_trace.pn_min_memory=req_mem[i];
            if(req_mem_per_cpu[i]==1){
                new_trace.pn_min_memory=new_trace.pn_min_memory|MEM_PER_CPU;
            }
        }
        
        
        strcpy(new_trace.features, as<const char*>(features[i]));
        strcpy(new_trace.gres, as<const char*>(gres[i]));
        
        if(shared[i]==NA_INTEGER){
            new_trace.shared=NO_VAL;
        }else{
            new_trace.shared=shared[i];
        }
        
        new_trace.cancelled=cancelled[i];
        
        write_single_trace(trace_file, &new_trace);
        /*written = write(trace_file, &new_trace, sizeof(new_trace));
        if (written != sizeof(new_trace)) {
            printf("Error writing to file: %d of %ld\n",
                   written, sizeof(new_trace));
            close(trace_file);
            return;
        }*/
    }
    fclose(trace_file);
            
    free(new_trace.username);
    free(new_trace.qosname);
    free(new_trace.partition);
    free(new_trace.account);
    free(new_trace.reservation);
    free(new_trace.dependency);
    free(new_trace.features);
    free(new_trace.gres);
        
    return;
}

///*** R
//timesTwo(42)
//*/
