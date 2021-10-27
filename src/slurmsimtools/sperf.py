import psutil
from collections import OrderedDict

def system_info():
    try:
        import cpuinfo
        m_cpu = cpuinfo.get_cpu_info()
        m_cpu["cpu_physical"] = psutil.cpu_count(logical=False)
        m_cpu["cpu_logical"] = psutil.cpu_count(logical=True)
    except:
        m_cpu = None
    try:
        import cpuinfo
        m_mem = {k:v for k,v in psutil.virtual_memory()._asdict().items()
                 if k in ('total','available')}
    except:
        m_mem = None

    info = {
        "cpu": m_cpu,
        "memory": m_mem
    }
    return info


def get_process_realtimestat(p):
    if p is None:
        return None
    r = OrderedDict()
    try:
        r['cpu_times'] = p.cpu_times()._asdict()
    except:
        r['cpu_times'] = None

    try:
        r['cpu_percent'] = p.cpu_percent()
    except:
        r['cpu_percent'] = None

    try:
        r['memory_info'] = p.memory_info()._asdict()
    except:
        r['memory_info'] = None

    try:
        r['io_counters'] = p.io_counters()._asdict()
    except:
        r['io_counters'] = None

    try:
        r['num_threads'] = p.num_threads()
    except:
        r['num_threads'] = None

    try:
        r['threads'] = [t._asdict() for t in p.threads()]
    except:
        r['threads'] = None

    return r
