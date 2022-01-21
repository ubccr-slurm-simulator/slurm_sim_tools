import argparse
from slurmsim import log


def add_command_archive(parent_parser):
    """
    compress output and logs
    """
    parser = parent_parser.add_parser('archive',  description=add_command_archive.__doc__)
    parser.add_argument('-np', default=1, type=int, help='number of parallel processes')
    parser.add_argument('-nt', default=1, type=int, help='parallel threads per file')
    parser.add_argument('top_dir', help='directory to look for file to archive')

    def handler(args):
        from slurmsim.archive import Archive
        print(args)

        Archive(args.top_dir, type='slurm_run', threads_per_file=args.nt, num_of_proc=args.np).run()

    parser.set_defaults(func=handler)


def add_command_process(parent_parser):
    """
    process commands
    """
    parser = parent_parser.add_parser('process', description=add_command_process.__doc__)
    subparsers = parser.add_subparsers(title=add_command_process.__doc__)

    add_command_process_slurmctrd_log(subparsers)


def add_command_process_slurmctrd_log(parent_parser):
    """
    process slurmctrd_log
    """
    parser = parent_parser.add_parser('slurmctrd_log',  description=add_command_process_slurmctrd_log.__doc__)

    parser.add_argument('-l', '--log', default="slurmctld.log.zst", type=str,
                        help="slurmctrd log")
    parser.add_argument('-csv', '--csv', default="slurmctld_log.csv.zst", type=str,
                        help="name of output csv file")
    parser.add_argument('--top-dir', help='recursively scan directory and process discovered slurmctrd log')
    parser.add_argument('-np', default=1, type=int, help='number of parallel processes')

    def handler(args):
        from slurmsim.process.slurmctld_log import process_slurmctrd_logs
        process_slurmctrd_logs(args.log, args.csv, args.top_dir, num_of_proc=args.np)
        #Archive(args.top_dir, type='slurm_run', threads_per_file=args.nt, processes=args.n).run()

    parser.set_defaults(func=handler)


def add_command_sacctlog(parent_parser):
    """
    manipulate sacct output
    """
    parser = parent_parser.add_parser('sacctlog', description=add_command_sacctlog.__doc__)
    subparsers = parser.add_subparsers(title=add_command_process.__doc__)

    add_command_sacctlog_format(subparsers)


def add_command_sacctlog_format(parent_parser):
    """
    format sacct output (can be compressed, determined by extension [.zst,.gz,.bz2,.xz])
    sacct output do not properly escape delimiters ("|"). This command will properly output csv file.

    it will also skip jobsteps and simplify simplify job states state (CANCELLED by user1->CANCELLED)
    """
    parser = parent_parser.add_parser('format',  description=add_command_sacctlog_format.__doc__)

    parser.add_argument('-ow', '--overwrite', action='store_true',
                        help="overwrite original file with formatted version")
    parser.add_argument('-o', '--output', default=None, type=str,
                        help="name of output file (default: addd _formatted suffix to base of input file)")
    parser.add_argument('-sep', '--sep', default="|", type=str,
                        help="output field separator")

    # header: bool = True, col_format: str = None, convert_data: bool = True, check_na = 'warning',
    # skip_jobsteps: bool = True, keep_scheduling_related = False, simplify_state = True)

    parser.add_argument('sacctlog', type=str, help='sacct log (output of sacct) to format')

    def handler(args):
        from slurmanalyser.sacctlog import format_sacctlog
        if args.overwrite:
            args.output = args.sacctlog
        format_sacctlog(args.sacctlog, output=args.output, sep=args.sep)

    parser.set_defaults(func=handler)


class CLI:
    """
    slurm sim command line interface
    """
    def __init__(self):
        short_log_prefix = True
        # import sys
        # if len(sys.argv) >= 3:
        #     i = 1
        #     while i+1 < len(sys.argv):
        #         if sys.argv[i] == "daemon" and sys.argv[i+1] in ("start", "startdeb"):
        #             short_log_prefix = False
        #         i = i + 1

        if short_log_prefix:
            log.basicConfig(
                level=log.INFO,
                format="[%(levelname)s] %(message)s"
            )
        else:
            log.basicConfig(
                level=log.INFO,
                format="[%(asctime)s - %(levelname)s] %(message)s"
            )

        self.root_parser = argparse.ArgumentParser(description='command line interface to slurm sim tools')
        self.root_parser.add_argument('-v', '--verbose', action='store_true',
                                      help="turn on verbose logging")
        self.root_parser.add_argument('-vv', '--very-verbose', action='store_true',
                                      help="turn on very verbose logging")

        self.subparsers = self.root_parser.add_subparsers(title='commands')

        self.verbose = False
        self.very_verbose = False

        add_command_archive(self.subparsers)
        add_command_process(self.subparsers)
        add_command_sacctlog(self.subparsers)

    def process_common_args(self, cli_args):
        """
        Process arguments common for all commands. Currently only verbose.
        """
        if "very_verbose" in cli_args and cli_args.very_verbose:
            log.verbose = True
            log.basicConfig(level=log.DEBUG // 2)
            log.getLogger().setLevel(log.DEBUG // 2)
            self.verbose = True
            self.very_verbose = True

        elif "verbose" in cli_args and cli_args.verbose:
            log.verbose = True
            log.basicConfig(level=log.DEBUG)
            log.getLogger().setLevel(log.DEBUG)
            self.verbose = True

    def run(self, args=None):
        """parse arguments and execute requested commands"""
        # PARSE: the command line parameters the user provided.
        cli_args = self.root_parser.parse_args(args=args)

        self.process_common_args(cli_args)

        # EXECUTE: the function provided in the '.set_defaults(func=...)'
        if hasattr(cli_args, "func"):
            return cli_args.func(cli_args)

        log.error("There is no command specified!")
        return None
