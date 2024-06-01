#!/usr/bin/env python3

import subprocess
import multiprocessing as mp
import sys
import os

# import magic: import all necessary modules from the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

if True:  # prevent autoformatting of the import block
    from objects import cluster
    from objects import task
    from ssh import ssh

## TODO: remove / fix legacy code
import threading
import queue
import time


def dispatcher(conn: mp.Queue, cluster: cluster.cluster_conf):
    while True:  # TODO: Continue writing here.
        time.sleep(0.1)  # prevent busy waiting

"""
## TODO: Everything below this line is legacy code and needs to be rewritten
def run_dispatcher(cluster: cluster_conf.cluster_conf, tasks: queue.Queue[task_list.task]):
    # Start a thread for each connection to every device (task_limit for each node). Then these start taking tasks from the queue.
    for node in cluster.node_list():
        for _ in range(node.get_task_limit()):
            threading.Thread(target=node_connection, args=(node, tasks)).start()

    tasks.join()  # wait for the queue to be emptied by all threads
    if not tasks.empty():
        sys.exit(1)


def remote_run(node: cluster_conf.cluster_conf.node_conf, tasks: task_list.task):
    try:

        ssh.Session(node.get_address()).connect().send_command_list([
            f"cd {task.w_dir}",
            f"./{task.env}/bin/activate",
            f"mkdir -p {task.out}",
            f"mkdir -p {task.err}",
            f"nice -n 19 {task.cmd} >{task.out}/{task.num}.out 2>{task.err}/{task.num}.err"
        ]).close()
        # log.debug(f"{task.cmd} >{task.out}/{task.num}.out 2>{task.err}/{task.num}.err &")  # TODO: remove
    except FileNotFoundError as e:  # file not found: program is not available
        tasks.put(task)  # reinsert task back into the queue
        break
    except subprocess.CalledProcessError as e:  # return code does not equal zero
        # log.error(f"error while executing command: {e}")
        if e.returncode == 255:  # return code 255 can only be returned by ssh
            # log.error(f"Assuming that the node ({node.get_address()}) is not reachable. Ending thread.")
            tasks.put(task)  # reinsert task back into the queue
            break
        else:
            # log.error(f"Executing command {task.num} failed: {task.cmd}")
    # else:
        # log.debug(f"Task {task.num} finished on node {node.get_address()}: {task.cmd}")
    finally:
        tasks.task_done() if has_task else None  # task from the queue always needs to be marked as done

"""
