__version__ = "0.0.2"

# a list of all the keys which have to be present in the task configuration file
task_necessary_keys = {
    "woking_directory",
    "environment",
    "output",
    "assign",
    "error",
    "executable",
    "var_arguments"
}

task_optional_keys = {
    "fix_arguments"
}
