sacctlog_header = "jobid,jobidraw,cluster,partition,account,group,gid,user,uid,\
submit,eligible,start,end,elapsed,exitcode,state,nnodes,ncpus,reqcpus,reqmem,\
reqtres,alloctres,timelimit,nodelist,jobname"

# slurm_int internal c-format withing slurm
sacctlog_header_to_slurm_int = {
    'jobid': 'jobid_str',
    'jobidraw': 'jobid_raw_str',
    'cluster': 'cluster',
    'partition': 'partition',
    'account': 'account',
    'group': 'group',
    'gid': 'gid',
    'user': 'user',
    'uid': 'uid',
    'submit': 'submit',
    'eligible': 'eligible',
    'start': 'start',
    'end': 'end',
    'elapsed': 'elapsed',
    'exitcode': 'exitcode',
    'state': 'state',
    'nnodes': 'nnodes',
    'ncpus': 'ncpus',
    'reqcpus': 'req_cpus',
    'reqmem': 'req_mem',
    'reqtres': 'req_tres',
    'alloctres': 'alloc_tres',
    'timelimit': 'timelimit',
    'nodelist': 'nodelist',
    'jobname': 'jobname',
}
from datetime import datetime, timedelta
from slurmanalyser.slurmparser import slurm_datetime, slurm_duration

slurm_int_value_convert = {
    'jobid_str': {'convert': str, 'default': ''},
    'jobid_raw_str': {'convert': str, 'default': ''},
    'cluster': {'convert': str, 'default': ''},
    'partition': {'convert': str, 'default': ''},
    'account': {'convert': str, 'default': ''},
    'group': {'convert': str, 'default': ''},
    'gid': {'convert': int, 'default': -1},
    'user': {'convert': str, 'default': ''},
    'uid': {'convert': int, 'default': -1},
    'submit': {'convert': slurm_datetime, 'default': datetime.min}, # Seconds since the Epoch. 2021-08-09T00:06:15
    'eligible': {'convert': slurm_datetime, 'default': datetime.min},
    'start': {'convert': slurm_datetime, 'default': datetime.min},
    'end': {'convert': slurm_datetime, 'default': datetime.min},
    'elapsed': {'convert': slurm_duration, 'default': timedelta()},
    'exitcode': {'convert': str, 'default': ''},
    'state': {'convert': str, 'default': ''},
    'nnodes': {'convert': int, 'default': -1}, # job->alloc_nodes step->nnodes job_comp->node_cnt, it can be tres count (slurmdb_find_tres_count_in_string)
    'ncpus': {'convert': int, 'default': -1},
    'req_cpus': {'convert': int, 'default': -1},
    'req_mem': {'convert': str, 'default': ''},
    'req_tres': {'convert': str, 'default': ''},
    'alloc_tres': {'convert': str, 'default': ''},
    'timelimit': {'convert': slurm_duration, 'default': timedelta()}, # can be string "UNLIMITED"/"Partition_Limit
    'nodelist': {'convert': str, 'default': ''},
    'jobname': {'convert': str, 'default': ''},
}

#for a in sacctlog_header_to_slurm_int.values():
    #print(f"'{a}': '{sacctlog_header_to_slurm_int.get(a,a)}',")
    #print(f"'{a}': {{'convert': str, 'default':''}},")



sacctlog_header = "jobid,jobidraw,cluster,partition,account,group,gid,user,uid,\
submit,eligible,start,end,elapsed,exitcode,state,nnodes,ncpus,reqcpus,reqmem,\
reqtres,alloctres,timelimit,nodelist,jobname"

lines=('6322435|6322435|ub-hpc|general-compute|account1|group1|100001|user1|200001|2021-08-09T00:06:15|2021-08-09T00:06:15|2021-08-09T00:06:42|2021-08-09T12:06:55|12:00:13|0:0|TIMEOUT|2|16|16|30000M|billing=16,cpu=16,mem=30000M,node=2|billing=16,cpu=16,mem=30000M,node=2|12:00:00|cpn-k07-05-[01-02]|jobname1',
'6322436|6322436|ub-hpc|general-compute|account2|group2|505796|user2|200002|2021-08-09T00:14:51|2021-08-09T00:14:51|2021-08-09T00:17:23|2021-08-09T00:22:28|00:05:05|0:0|COMPLETED|1|12|12|187000M|billing=12,cpu=12,mem=187000M,node=1|billing=12,cpu=12,mem=187000M,node=1|3-00:00:00|cpn-f07-05|jobname2')



for k,v in slurm_int_value_convert.items():
    print(f"        self.{k} = {repr(slurm_int_value_convert[k]['default'])}")

slurm_int_to_sacctlog_header = {v:k for k,v in sacctlog_header_to_slurm_int.items()}
for k,v in slurm_int_value_convert.items():
    if k == slurm_int_to_sacctlog_header[k]:
        print(
            f"'{k}': {{'convert': {v['convert'].__name__}}},")
    else:
        print(
            f"'{k}': {{'convert': {v['convert'].__name__}, 'sacctlog_name': {repr(slurm_int_to_sacctlog_header[k])}}},")


# python mimicing of job_id printing
def print_job_id(obj_type, obj):
    job = obj
    step = obj
    job_comp = obj

    if obj_type == "JOB":
        job = obj
    elif obj_type == "JOBSTEP":
        job = step.job_ptr
    elif obj_type == "JOBCOMP":
        job = None
        step = None

    if job:
        if job.array_task_str:
            m_id = "%u_[%s]" % (job.array_job_id, job.array_task_st)
        elif job.array_task_id:
            m_id = "%u_[%u]" % (job.array_job_id, job.array_task_id)
        elif job.het_job_id:
            m_id ="%u+%u" % (job.jet_job_id, job.het_job_offset);
            m_id ="%u" % job.jobid

    if obj_type == "JOB":
        tmp_char = m_id;
    elif obj_type == "JOBSTEP":
        if step.stepid == "SLURM_BATCH_SCRIPT":
            tmp_char = "%s.batch" % m_id
        elif step.stepid == "SLURM_EXTERN_CONT":
            tmp_char = "%s.extern" % m_id
        else:
            tmp_char = "%s.%u" % (m_id, step.stepid)
    elif obj_type == "JOBCOMP":
        tmp_char = "%u" % job_comp.jobid
    return tmp_char




# python mimicing of job_id_raw printing
def print_job_id_raw(obj_type, obj):
    job = obj
    step = obj
    job_comp = obj

    if obj_type == "JOB":
        tmp_char = "%u" % job.jobid
    elif obj_type == "JOBSTEP":
        if step.stepid == "SLURM_BATCH_SCRIPT":
            tmp_char = "%u.batch" % step.job_ptr.jobid
        elif step.stepid == "SLURM_EXTERN_CONT":
            tmp_char = "%u.extern" % step.job_ptr.jobid
        else:
            tmp_char = "%u.%u" % (step.job_ptr.jobid, step.stepid)
    elif obj_type == "JOBCOMP":
        tmp_char = "%u" % job_comp.jobid

    return tmp_char


MEM_PER_CPU = 0x8000000000000000
NO_VAL64 = 0xfffffffffffffffe
NO_VAL = 0xfffffffe

"""
/*
 * Convert number from one unit to another.
 * By default, Will convert num to largest divisible unit.
 * Appends unit type suffix -- if applicable.
 *
 * IN num: number to convert.
 * OUT buf: buffer to copy converted number into.
 * IN buf_size: size of buffer.
 * IN orig_type: The original type of num.
 * IN spec_type: Type to convert num to. If specified, num will be converted up
 * or down to this unit type.
 * IN divisor: size of type 1000 or 1024
 * IN flags: flags to control whether to convert exactly or not at all.
 */
 
 /* unit types */
enum {
	UNIT_NONE,
	UNIT_KILO,
	UNIT_MEGA,
	UNIT_GIGA,
	UNIT_TERA,
	UNIT_PETA,
	UNIT_UNKNOWN
};
 """
def convert_num_unit2(num: float, orig_type: int, spec_type: int, divisor:int,  flags):
    # orig_type='UNIT_MEGA', spec_type=NO_VAL devisor=1024 ,flags 'CONVERT_NUM_UNIT_EXACT'
    #

    if not flags in ('CONVERT_NUM_UNIT_RAW', 'CONVERT_NUM_UNIT_NO', 'CONVERT_NUM_UNIT_EXACT'):
        raise ValueError(f"unknown flags {flags}")

    unit = "\0KMGTP?"

    if num == 0:
        return '0'

    if spec_type != NO_VAL:
        # spec_type overrides all flags
        if spec_type < orig_type:
            while spec_type < orig_type:
                num *= divisor
                orig_type-=1
        
        elif spec_type > orig_type:
            while spec_type > orig_type:
                num /= divisor
                orig_type+=1
    elif flags == 'CONVERT_NUM_UNIT_RAW':
        orig_type = 'UNIT_NONE'
    elif flags == 'CONVERT_NUM_UNIT_NO':
        # no op
        pass
    elif flags == 'CONVERT_NUM_UNIT_EXACT':
        # convert until we would loose precision */
        # half values  (e.g., 2.5G) are still considered precise */

        while num >= divisor and num % (divisor // 2) == 0:
            num /= divisor
            orig_type+=1
    else:
        #/* aggressively convert values */
        while num >= divisor:
            num /= divisor
            orig_type+=1

    if orig_type < 0 || orig_type > 5:
        # i.e. outside of KMGTP range
        orig_type = 'UNIT_UNKNOWN'

    #/* Here we are checking to see if these numbers are the same,
    # * meaning the float has not floating point.  If we do have
    # * floating point print as a float.
    #*/
    if float(int(num)) == num:
        return f"{int(num):d}{unit[orig_type]}"
    else:
        return f"{int(num):.2f}{unit[orig_type]}

def convert_num_unit(num, orig_type, spec_type, flags):
    return convert_num_unit2(num, orig_type, spec_type, 1024, flags)

# python mimicing of req mem printing
def print_req_mem(obj_type, obj):

    job = obj
    step = obj
    job_comp = obj

    if obj_type == "JOB":
        tmp_uint64 = job.req_mem
    elif obj_type == "JOBSTEP":
        tmp_uint64 = step.job_ptr.req_mem
    elif obj_type == "JOBCOMP":
        tmp_uint64 = NO_VAL64

    if tmp_uint64 != NO_VAL64:
        per_cpu = False
        if tmp_uint64 & MEM_PER_CPU:
            tmp_uint64 = tmp_uint64 & (~MEM_PER_CPU)
            per_cpu = True


        outbuf = convert_num_unit(float(tmp_uint64), 'UNIT_MEGA', units=NO_VAL, 'CONVERT_NUM_UNIT_EXACT')
        if per_cpu:
            outbuf+="c"
        else:
            outbuf+="n"
    return tmp_char

