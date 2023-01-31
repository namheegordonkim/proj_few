import os
import sys
from argparse import ArgumentParser
from shutil import copy2, copytree

import pandas as pd
import gspread
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials

"""
Usage: python smart_run.py [--sbatch_yes or -s] [--overwrite_yes or -o] run_1 [run_2] [run_3]
Must be run from the project root.

Reads the latest configuration from the experiment management spreadsheet on Google Drive.
Then, translates the cells corresponding to existing configurations to a runnable python commands.
The python commands are saved into the subdirectory named `submits` as .sh files.
Then the specified configuration (given as argument) is executed after the following bookkeeping steps:
1. If not already existing, create a subdirectory under `runs` whose name is the same as the given configuration
2. Copy the most up-to-date `src` into the subdirectory
3. Execute `run.sh` inside the copied `src` in conjunction with the .sh file in `submits`.

Stays agnostic to how exactly the training runs are configured.
Assumes that `run.sh` or a script similar to that kind manages this.
"""

SBATCH_OPTIONS = """
--time=4:0:0
--mem=16gb
--gres=gpu:1
--constraint=\"pascal|volta|a100\"
"""


def main(args):
    # if args.debug_yes:
    #     input()  # to allow for debugger attaching

    # Use credentials to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('/home/nhgk/workspace/cred.json', scope)
    client = gspread.authorize(credentials)

    # Open the spreadsheet using the file ID
    spreadsheet_id = '1YhlpAA3x8GEzg8NslpL3QY47yd4q1Y8dfr0FhNj8NL0'

    spreadsheet = client.open_by_key(spreadsheet_id)

    # Export the first worksheet as CSV
    worksheet = spreadsheet.get_worksheet(0)

    df = pd.DataFrame(worksheet.get_all_values())

    for cell_name in args.cell_names:
        mask = df.eq(cell_name)
        if mask.any().any():
            # Find the first cell that contains the value "hello"
            row, col = np.argwhere(mask.values)[0]

            # Select all the rows from the same column
            column = df.iloc[:, col]

            # Join the strings in that column using the space character as the separator
            final_string = column.iloc[:10].str.cat(sep=" ")
        else:
            # The value "hello" was not found in the dataframe
            final_string = None

        # create the executable python command and store it into a .sh file within `submits`
        command = final_string
        if args.debug_yes:
            command += " ++debug_yes=True"
        bash_run_command_string = f"#!/bin/bash\nbash run.sh {command}"

        # with open(f"submits/{cell_name}.sh", "w") as f:
        #     f.write(f"#!/bin/bash\n{command}")

        # debug run vs. non-debug run: debug run doesn't do source copying
        if args.debug_yes:
            os.chdir(f"./src")
            with open("command.sh", "w") as f:
                f.write(bash_run_command_string)
            if args.sbatch_yes:
                os.system(f"sbatch {SBATCH_OPTIONS} command.sh")
            else:
                os.system(f"bash command.sh")
        else:
            # now that we have the commands to run, we create the run directory within `runs`
            os.makedirs(f"runs/{cell_name}", exist_ok=True)
            # if overwrite is specified, then we should replace the source
            if not os.path.exists(f"runs/{cell_name}/src") or args.overwrite_yes:
                copytree("./src", f"runs/{cell_name}/src", dirs_exist_ok=True)
            # otherwise we don't copy because we want to preserve old behaviour (useful if this is a re-run or sanity check)

            os.chdir(f"runs/{cell_name}/src")
            with open("command.sh", "w") as f:
                f.write(bash_run_command_string)
            if args.sbatch_yes:
                os.system(f"sbatch {SBATCH_OPTIONS} command.sh")
            else:
                os.system(f"bash command.sh")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--sbatch_yes", "-s", action="store_true")
    parser.add_argument("--overwrite_yes", "-o", action="store_true")
    parser.add_argument("--debug_yes", "-d", action="store_true")  # if set, will pause the program
    parser.add_argument("cell_names", metavar="N", type=str, nargs="+")
    args = parser.parse_args()
    main(args)
