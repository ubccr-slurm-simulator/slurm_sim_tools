from slurmanalyser.slurmparser import SlurmFileParser
from pprint import pprint

SLURMDB_FS_USE_PARENT = 0x7FFFFFFF

class SlurmAccounts:
    def __init__(self):
        # Slurm config lines
        self.lines = []
        self.records = []
        self.cluster = None
        self.account = {}
        self.root = None
        self.user = {}
        self.qos = {}

    @staticmethod
    def from_file(sacctmgr_dump: str, sacctmgr_qos: str):
        slurm_acct = SlurmAccounts()

        slurm_acct.read_sacctmgr_qos(sacctmgr_qos)
        slurm_acct.read_sacctmgr_dump(sacctmgr_dump)

        return slurm_acct

    def parse_sacctmgr_dump(self, lines: list[str]):
        self.lines = lines
        parent = None

        for line in lines:
            line = line.strip()
            if line == "":
                continue
            if line[0] == "#":
                continue

            variable, value = SlurmFileParser.split_expr(line, split="-")
            if variable == "Parent":
                parent = value.strip("'").strip('"')
            else:
                val0, val1plus = SlurmFileParser.split_expr(value, pretty_left=False, split=":")
                val0 = val0.strip("'").strip('"')
                m_dict = dict(SlurmFileParser.split_expr_array(val1plus, ":",convert_values=True))
                if 'QOS' in m_dict:
                    if m_dict['QOS']!='':
                        m_dict['QOSAdd']=set()
                        m_dict['QOSRemove'] = set()
                        for qos in m_dict['QOS'].split(","):
                            if qos[0] == "+":
                                qos_name = qos[1:]
                                m_dict['QOSAdd'].add(qos_name)
                            elif qos[0] == "-":
                                qos_name = qos[1:]
                                m_dict['QOSRemove'].add(qos_name)
                            else:
                                qos_name = qos
                                m_dict['QOSAdd'].add(qos_name)
                            if qos_name not in self.qos:
                                print(f"Warning: {qos_name} not in QOS list")
                    del m_dict['QOS']

                if variable == 'Cluster':
                    self.cluster = m_dict
                if variable == 'User':
                    if val0 == 'root':
                        self.root = m_dict
                    if 'Fairshare' in m_dict and str(m_dict['Fairshare']).isdigit():
                        if int(m_dict['Fairshare']) == SLURMDB_FS_USE_PARENT:
                            m_dict['Fairshare'] = 'parent'

                    m_dict['Parent'] = parent
                    self.user[val0] = m_dict
                if variable == 'Account':
                    self.account[val0] = m_dict

    def read_sacctmgr_dump(self, filename):
        lines = SlurmFileParser.read_lines_from_file(filename)
        self.parse_sacctmgr_dump(lines)

    @staticmethod
    def convert_qos_value(key:str, value: str):
        if key in ('MaxSubmitPU', 'Priority'):
            return int(value)
        elif key in ('UsageFactor',):
            return float(value)
        else:
            return value

    def read_sacctmgr_qos(self, filename):
        import csv
        with open(filename, newline='') as csvfile:
            csv_list = list(csv.reader(csvfile, delimiter='|'))
            names = csv_list[0]
            self.qos = {v[0]: {names[i]: SlurmAccounts.convert_qos_value(names[i], f)
                               for i, f in enumerate(v) if f != "" and names[i] != ""}
                        for v in csv_list[1:]}
