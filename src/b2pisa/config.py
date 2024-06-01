__version__ = "0.1.5"

# Number of parallel listeners on the daemon socket
daemon_listeners = 20
daemon_pidfile = "/tmp/b2pisad.pid"
daemon_sockfile = "/tmp/b2pisad.sock"

# TODO: The lines below are not refactored yet!
# a list of all the keys which have to be present in the task configuration file
task_necessary_keys = {
    "woking_directory",
    "environment",
    "output",
    "assign",
    "executable",
    "var_arguments"
}

task_optional_keys = {
    "fix_arguments"
}
