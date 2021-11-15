
def test_job_sacct_log():
    import datetime
    import slurmanalyser.sacctlog
    lines = (
        '6322435|6322435|ub-hpc|general-compute|account1|group1|100001|user1|200001|2021-08-09T00:06:15|2021-08-09T00:06:15|2021-08-09T00:06:42|2021-08-09T12:06:55|12:00:13|0:0|TIMEOUT|2|16|16|30000M|billing=16,cpu=16,mem=30000M,node=2|billing=16,cpu=16,mem=30000M,node=2|12:00:00|cpn-k07-05-[01-02]|jobname1',
        '6322436|6322436|ub-hpc|general-compute|account2|group2|505796|user2|200002|2021-08-09T00:14:51|2021-08-09T00:14:51|2021-08-09T00:17:23|2021-08-09T00:22:28|00:05:05|0:0|COMPLETED|1|12|12|187000M|billing=12,cpu=12,mem=187000M,node=1|billing=12,cpu=12,mem=187000M,node=1|3-00:00:00|cpn-f07-05|jobname2')

    r1 = slurmanalyser.sacctlog.JobSacctLog.from_line(lines[0])
    check = {
        'user': 'user1',
        'uid': 200001,
        'submit': datetime.datetime(2021,8,9,0,6,15),
        'elapsed': datetime.timedelta(hours=12, minutes=00, seconds=13)
    }
    for k,v in check.items():
        assert r1.__getattribute__(k) == v

    r2 = slurmanalyser.sacctlog.JobSacctLog.from_line(lines[1])



