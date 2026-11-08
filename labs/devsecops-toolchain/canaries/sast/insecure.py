import subprocess

DB_PASSWORD = "hunter2"


def export(name):
    return subprocess.call("tar czf /tmp/" + name + ".tgz /data", shell=True)
