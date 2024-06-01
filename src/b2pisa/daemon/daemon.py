import argparse
import atexit
import logging as log
import os
import socket
import sys
import time
import signal
import multiprocessing as mp

# import magic: import all necessary modules from the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

if True:  # prevent autoformatting of the import block
    import config
    from dispatcher import dispatcher
    from objects import cluster
    from objects import task


class Daemon:
    """
    Attributes
    ----------
    pidfile : str
        Path to the pidfile
    sock : str
        Path to the socket file
    stdout : str, optional
        Path to the file to redirect stdout to, default is /dev/null
    stderr : str, optional
        Path to the file to redirect stderr to, default is /dev/null

    Methods
    -------
    start : None
        Start the daemon
    stop : None
        Stop the daemon
    restart : None
        Restart the daemon

    This class provides the possibility to create a daemon process.
    The daemon process writes its PID to a pidfile and listens on a socket.
    The daemon is either started from a program. There can only be one instance of the daemon running at a time.
    The daemon can be stopped, restarted and started again from another program.
    """

    def __init__(self, pidfile: str, sockfile: str, cluster: cluster.cluster_conf, stdout: str = None, stderr: str = None):
        self.stdout = os.devnull if stdout is None else stdout
        self.stderr = os.devnull if stderr is None else stderr
        self.pidfile = pidfile
        self.sockfile = sockfile
        self.cluster = cluster

        # set start method for new processes to spawn to avoid issues with fork (which is becoming deprecated)
        mp.set_start_method('spawn')

    def _daemonize(self):
        # Step 1: Fork, exit the parent and continue within the child
        if os.fork():
            sys.exit(0)

        # Step 2: Decouple from the parent environment
        os.chdir("/")  # cd to root to avoid blocking any mount points
        os.setsid()  # create a new session and set child process as session leader
        os.umask(0)  # set the file creation mask to 0 to be independent of parent process

        # Step 3: Fork the second time to ensure the daemon process is not a session leader
        if os.fork():
            sys.exit(0)

        # Step 4: shut down stdin
        with open(os.devnull, 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())

        # Step 5: redirect stderr first to print possible error messages when redirecting stdout
        sys.stderr.flush()
        with open(self.stderr, 'wb+', 0) as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        # Step 6: redirect stdout
        sys.stdout.flush()
        with open(self.stdout, 'wb+', 0) as stdout:
            os.dup2(stdout.fileno(), sys.stdout.fileno())

        # Step 7: write pidfile
        atexit.register(self._delpid)
        with open(self.pidfile, "w+") as pidfile:
            pidfile.write(f"{str(os.getpid())}")

    def _setup_socket(self):
        self._cleanup_socket()  # remove potential old socket file

        # create a socket to listen on
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.umask(0o177)  # create socket with rights: srw-------
            self.sock.bind(self.sockfile)
        except OSError as e:
            print(f"Could not bind to socket: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            os.umask(0)  # reset umask to default value
        self.sock.listen(config.daemon_listeners)  # maximum of connections

        atexit.register(self._socket_end)  # cleanup socket when daemon is stopped

    def _socket_end(self):  # close socket when daemon is stopped
        self.sock.close()
        self._cleanup_socket()

    def _start_dispatcher(self):
        self.conn_dispatcher = mp.Queue()
        atexit.register(lambda: self.conn_dispatcher.close())  # close queue when daemon is stopped
        self.dispatcher = mp.Process(target=dispatcher.dispatcher, args=(self.conn_dispatcher, self.cluster,), daemon=True)  # initialise dispatcher and make sure it gets killed with the daemon
        self.dispatcher.start()

    def _delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def _cleanup_socket(self):
        # clean up (old) socket file if exists
        if os.path.exists(self.sockfile):
            os.remove(self.sockfile)

    def _get_pid_from_file(self):
        try:
            with open(self.pidfile, 'r') as pf:
                return int(pf.read().strip())
        except IOError:
            return None

    def _receive_task(self):
        pass  # TODO

    def start(self):
        # Check for a pidfile to see if the daemon already runs
        if self._get_pid_from_file():
            print("Daemon is already running.", file=sys.stderr)
            sys.exit(1)

        # make sure all cleanup methods are called when the daemon is stopped
        signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

        # Start the daemon
        self._daemonize()
        self._setup_socket()
        self._start_dispatcher()
        self._run()

    def stop(self, del_output: bool = False):
        # Get the pid from the pidfile
        pid = self._get_pid_from_file()
        if not pid:
            print("Daemon is not running.", file=sys.stderr)
            sys.exit(1)

        # kill daemon
        try:
            while True:
                os.kill(pid, signal.SIGTERM)  # send SIGTERM signal to the daemon
                time.sleep(0.1)
        except OSError as e:
            err = str(e)
            if err.find("No such process") > 0:  # daemon is not running (anymore)
                self._delpid()  # clean up and remove PID file
                self._cleanup_socket()  # clean up and remove socket file
                if del_output:
                    if os.path.exists(self.stdout) and self.stdout != os.devnull:
                        os.remove(self.stdout)
                    if os.path.exists(self.stderr) and self.stderr != os.devnull:
                        os.remove(self.stderr)
            else:  # unknown error
                print(str(e), file=sys.stderr)
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

    def _run(self):
        """The main loop of the daemon."""
        while True:
            client, address = self.sock.accept()  # blocking call, wait for client to connect
            # TODO: Continue starting a new process to read from socket and add data to queue


def start_daemon():
    """
    This function is a necessary entry point for the application. This makes it possible to call the daemon application like an executable.
    To enable this feature the pyproject.toml file needs to contain a function which can be called by the python interpreter.
    """

    # set up argument parser
    parser = argparse.ArgumentParser(
        prog="b2pisad",
        description="b2pisa daemon"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {config.__version__}")
    parser.add_argument("-c", "--cluster", help="cluster configuration file")
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug output")
    parser.add_argument("-s", "--stop", action="store_true", help="stop the daemon")
    args = parser.parse_args()

    if args.stop:  # only stop the daemon
        daemon = Daemon(config.daemon_pidfile, config.daemon_sockfile, None)
        daemon.stop(del_output=True)
        sys.exit(0)

    # no stopping of the daemon -> start the daemon
    log.basicConfig(
        level=log.DEBUG if args.debug else log.WARNING,
        # format="%(acsctime)s - %(levelname)s - %(message)s",
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if hasattr(args, "cluster") and args.cluster is None:
        log.error("No cluster configuration file set, cannot start daemon")
        sys.exit(1)
    cluster_conf = cluster.parse_file(args.cluster)

    # initialise and start the daemon
    daemon = Daemon(config.daemon_pidfile, config.daemon_sockfile, cluster_conf)
    daemon.start()


if __name__ == "__main__":
    start_daemon()
