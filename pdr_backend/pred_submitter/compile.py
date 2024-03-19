import json
import os
from solcx import install_solc, compile_files


def list_files(directory):
    """
    List all files and their full paths in the given directory.

    :param directory: Path to the directory whose files we want to list.
    :return: A list of tuples, each containing the file name and its full path.
    """
    files_list = []
    # Walk through all directories and files in the given directory
    for root, _, files in os.walk(directory):
        for file in files:
            # Append the file and its full path to the list
            files_list.append(os.path.join(root, file))
    return files_list


def compile_contracts():
    install_solc(version="0.8.13")
    files = list_files("./pdr_backend/prediction_manager/contracts/")
    print("Compiling:", files)
    compiled = compile_files(
        files,
        output_values=["abi", "bin"],
        solc_version="0.8.13",
        optimize=True,
        optimize_runs=1000,
    )

    output_dir = os.path.join(os.path.dirname(__file__), "compiled_contracts")
    print(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate over the compiled contracts
    for contract_name, contract_data in compiled.items():
        # Define filenames for the ABI and bytecode
        base_contract_name = os.path.basename(contract_name).split(":")[1]
        abi_filename = os.path.join(output_dir, f"{base_contract_name}_abi.json")
        bytecode_filename = os.path.join(
            output_dir, f"{base_contract_name}_bytecode.bin"
        )

        # Write the ABI to a file
        with open(abi_filename, "w") as abi_file:
            json.dump(contract_data["abi"], abi_file)

        # Write the bytecode to a file
        if len(contract_data["bin"]) > 10:
            with open(bytecode_filename, "w") as bytecode_file:
                bytecode_file.write(contract_data["bin"])

    print(f"ABI and bytecode files have been saved to {output_dir}/")


if __name__ == "__main__":
    compile_contracts()
