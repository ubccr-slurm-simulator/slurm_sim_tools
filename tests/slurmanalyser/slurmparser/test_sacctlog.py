
def test_job_sacct_log(datadir):
    import slurmanalyser.sacctlog
    import pandas as pd
    import numpy as np

    for filename, filename_ref in (('sacct_dump2101.log','sacctlog_dump2101_str.pkl'),('sacct_dump2110.log','sacctlog_dump2110_str.pkl')):
        sacctlog = slurmanalyser.sacctlog.SacctLog.from_logfile(str(datadir / filename), convert_data=False)
        df_ref = pd.read_pickle(str(datadir / filename_ref))

    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.width', None)
    # print(sacctlog.df)
    # print(df_ref)
    # print( np.all(sacctlog.df == df_ref))
    #assert sacctlog.df == df_ref

    #sacctlog = slurmanalyser.sacctlog.SacctLog.from_file(str(datadir / 'sacct_dump2110.log'), convert_data=False)
    #sacctlog.df.to_pickle('/home/nikolays/slurm_sim_ws/slurm_sim_tools/tests/slurmanalyser/slurmparser/test_sacctlog/sacctlog_dump2110_str.pkl')

