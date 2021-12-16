
class CLI:
    """
    slurm sim command line interface
    """
    def __init__(self):
        import sys

        short_log_prefix = True
        if len(sys.argv) >= 3:
            i = 1
            while i+1 < len(sys.argv):
                if sys.argv[i] == "daemon" and sys.argv[i+1] in ("start", "startdeb"):
                    short_log_prefix = False
                i = i + 1

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

        self.root_parser = argparse.ArgumentParser(description='command line interface to AKRR')
        self.root_parser.add_argument('-v', '--verbose', action='store_true', help="turn on verbose logging")
        self.root_parser.add_argument('-vv', '--very-verbose', action='store_true', help="turn on very verbose logging")

        self.subparsers = self.root_parser.add_subparsers(title='commands')

        from .commands import add_command_daemon
        add_command_daemon(self.subparsers)

        from .commands import add_command_setup
        add_command_setup(self.subparsers)

        from .commands import add_command_resource
        add_command_resource(self.subparsers)

        from .commands import add_command_app
        add_command_app(self.subparsers)

        from .commands import add_command_task
        add_command_task(self.subparsers)

        from .commands import add_command_archive
        add_command_archive(self.subparsers)

        from .commands import add_command_update
        add_command_update(self.subparsers)

        self.verbose = False

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
