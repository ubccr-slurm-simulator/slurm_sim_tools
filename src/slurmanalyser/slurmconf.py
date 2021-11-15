import re
from pprint import pprint
from collections import OrderedDict
from hostlist import expand_hostlist



class SlurmConf:
    def __init__(self):
        # Slurm config lines
        self.lines = []
        # nodes
        self.node = dict()
        # partitions
        self.partition = dict()

    @staticmethod
    def from_file(filename: str):
        from slurmanalyser.slurmparser import SlurmFileParser
        slurm_conf = SlurmConf()
        lines = SlurmFileParser.read_lines_from_file(filename)
        slurm_conf.parse_conf(lines)
        return slurm_conf

    def parse_conf(self, lines: list[str]):
        from slurmanalyser.slurmparser import SlurmFileParser
        self.lines = lines
        default_node_name = dict()
        default_partition_name = dict()

        self.node = dict()
        self.partition = dict()

        for line in lines:
            line = line.strip()
            if line == "":
                continue
            if line[0] == "#":
                continue

            variable, value = SlurmFileParser.split_expr(line)
            if variable == "NodeName":
                val0, val1plus = SlurmFileParser.split_expr(value, pretty_left=False, split=" ")
                dict1 = dict(SlurmFileParser.split_expr_array(val1plus))
                if val0.lower() == "default":
                    default_node_name.update(dict1)
                else:
                    dict_merged = dict(NodeNamesShort=val0, NodeNamesExpanded=set(expand_hostlist(val0)))
                    dict_merged.update(default_node_name)
                    dict_merged.update(dict1)
                    for node in dict_merged['NodeNamesExpanded']:
                        self.node[node] = dict_merged
            if variable == "PartitionName":
                val0, val1plus = SlurmFileParser.split_expr(value, pretty_left=False, split=" ")
                dict1 = dict(SlurmFileParser.split_expr_array(val1plus))
                if val0.lower() == "default":
                    default_partition_name.update(dict1)
                else:
                    dict_merged = dict(PartitionName=val0)
                    dict_merged.update(default_partition_name)
                    dict_merged.update(dict1)
                    dict_merged['NodeNamesShort'] = dict1['Nodes']
                    dict_merged['NodeNamesExpanded'] = set(expand_hostlist(dict1['Nodes']))
                    del dict_merged['Nodes']
                    self.partition[val0] = dict_merged
        # post process
