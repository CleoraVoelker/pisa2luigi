import atexit
import os
import socket
import sys
import time
from signal import SIGTERM


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

    def __init__(self, pidfile, sockfile, stdout=None, stderr=None):
        self.stdout = os.devnull if stdout is None else stdout
        self.stderr = os.devnull if stderr is None else stderr
        self.pidfile = pidfile
        self.sockfile = sockfile

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

        """
        # daemonizing done, now configure socket
        self._cleanup_socket()  # remove potential old socket file

        # create a socket to listen on
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.sockfile)
        self.sock.listen(1)
        """

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

    def start(self):
        # Check for a pidfile to see if the daemon already runs
        if self._get_pid_from_file():
            print("Daemon is already running.", file=sys.stderr)
            sys.exit(1)  # evtl. Return Error?

        # Start the daemon
        self._daemonize()
        self.run()

    def stop(self, del_output=True):
        # Get the pid from the pidfile
        pid = self._get_pid_from_file()
        if not pid:
            print("Daemon is not running.", file=sys.stderr)
            return

        # kill daemon
        try:
            while True:
                os.kill(pid, SIGTERM)  # send SIGTERM signal to the daemon
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

    def run(self):
        """Override this method in your subclass"""
        while True:
            print("Daemon is running")
            time.sleep(1)
