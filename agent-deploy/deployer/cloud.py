from abc import ABC, abstractmethod
import shutil
import subprocess


def run_command(command):
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error executing {' '.join(command)}: {result.stderr}")
    return result.stdout

