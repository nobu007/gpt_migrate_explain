import os
import time
from collections import defaultdict

import typer
from ai import AI
from steps.debug import debug_error, debug_testfile
from steps.migrate import add_env_files, get_dependencies, write_migration
from steps.setup import create_environment
from steps.test import create_tests, run_dockerfile, run_test, validate_tests
from utils import build_directory_structure, detect_language

app = typer.Typer()


class Globals:
    def __init__(
        self,
        sourcedir,
        targetdir,
        sourcelang,
        targetlang,
        sourceentry,
        source_directory_structure,
        operating_system,
        testfiles,
        sourceport,
        targetport,
        guidelines,
        ai,
    ):
        self.sourcedir = sourcedir
        self.targetdir = targetdir
        self.sourcelang = sourcelang
        self.targetlang = targetlang
        self.sourceentry = sourceentry
        self.source_directory_structure = source_directory_structure
        self.operating_system = operating_system
        self.testfiles = testfiles
        self.sourceport = sourceport
        self.targetport = targetport
        self.guidelines = guidelines
        self.ai = ai


@app.command()
def main(
    model: str = typer.Option(
        "gemini/gemini-1.5-flash",
        help="Large Language Model to be used. Default is 'gemini/gemini-1.5-flash'. To use OpenAI directly with your API key, use 'gpt-4-32k'.",
    ),
    temperature: float = typer.Option(0, help="Temperature setting for the AI model."),
    sourcedir: str = typer.Option(
        "../benchmarks/flask-nodejs/source", help="Source directory containing the code to be migrated."
    ),
    sourcelang: str = typer.Option(None, help="Source language or framework of the code to be migrated."),
    sourceentry: str = typer.Option(
        "app.py",
        help="Entrypoint filename relative to the source directory. For instance, this could be an app.py or main.py file for Python.",
    ),
    targetdir: str = typer.Option(
        "../benchmarks/flask-nodejs/target", help="Directory where the migrated code will live."
    ),
    targetlang: str = typer.Option("nodejs", help="Target language or framework for migration."),
    operating_system: str = typer.Option(
        "linux", help="Operating system for the Dockerfile. Common options are 'linux' or 'windows'."
    ),
    testfiles: str = typer.Option(
        "app.py",
        help="Comma-separated list of files that have functions to be tested. For instance, this could be an app.py or main.py file for Python app where your REST endpoints are. Include the full relative path.",
    ),
    sourceport: int = typer.Option(
        None, help="(Optional) port for testing the unit tests file against the original app."
    ),
    targetport: int = typer.Option(8080, help="Port for testing the unit tests file against the migrated app."),
    guidelines: str = typer.Option(
        "",
        help='Stylistic or small functional guidelines that you\'d like to be followed during the migration. For instance, "Use tabs, not spaces".',
    ),
    step: str = typer.Option("all", help="Step to run. Options are 'setup', 'migrate', 'test', 'all'."),
):
    ai = AI(
        model=model,
        temperature=temperature,
    )

    sourcedir = os.path.abspath(sourcedir)
    targetdir = os.path.abspath(targetdir)
    os.makedirs(targetdir, exist_ok=True)

    detected_language = sourcelang or detect_language(sourcedir)

    if not sourcelang:
        if detected_language:
            is_correct = typer.confirm(f"Is your source project a {detected_language} project?")
            if is_correct:
                sourcelang = detected_language
            else:
                sourcelang = typer.prompt("Please enter the correct language for the source project")
        else:
            sourcelang = typer.prompt("Unable to detect the language of the source project. Please enter it manually")

    if not os.path.exists(os.path.join(sourcedir, sourceentry)):
        sourceentry = typer.prompt(
            "Unable to find the entrypoint file. Please enter it manually. This must be a file relative to the source directory."
        )

    source_directory_structure = build_directory_structure(sourcedir)
    globals = Globals(
        sourcedir,
        targetdir,
        sourcelang,
        targetlang,
        sourceentry,
        source_directory_structure,
        operating_system,
        testfiles,
        sourceport,
        targetport,
        guidelines,
        ai,
    )

    typer.echo(
        typer.style(
            f"◐ Reading {sourcelang} project from directory '{sourcedir}', with entrypoint '{sourceentry}'.",
            fg=typer.colors.BLUE,
        )
    )
    time.sleep(0.3)
    typer.echo(
        typer.style(
            f"◑ Outputting {targetlang} project to directory '{targetdir}'.",
            fg=typer.colors.BLUE,
        )
    )
    time.sleep(0.3)
    typer.echo(typer.style("Source directory structure: \n\n" + source_directory_structure, fg=typer.colors.BLUE))

    """ 1. Setup """
    if step in ["setup", "all"]:
        # Set up environment (Docker)
        create_environment(globals)

    """ 2. Migration """
    if step in ["migrate", "all"]:
        target_deps_per_file = defaultdict(list)

        def migrate(sourcefile, globals, parent_file=None):
            # recursively work through each of the files in the source directory, starting with the entrypoint.
            internal_deps_list, external_deps_list = get_dependencies(sourcefile=sourcefile, globals=globals)
            for dependency in internal_deps_list:
                migrate(dependency.strip(), globals, parent_file=sourcefile)
            file_name = write_migration(
                sourcefile,
                external_deps_list,
                target_deps_per_file.get(sourcefile),
                globals,
            )
            target_deps_per_file[parent_file].append(file_name)

        migrate(sourceentry, globals)
        add_env_files(globals)

    """ 3. Testing """
    if step in ["test", "all"]:
        while True:
            result = run_dockerfile(globals)
            if result == "success":
                break
            debug_error(result, "", globals)
        for testfile in globals.testfiles.split(","):
            generated_testfile = create_tests(testfile, globals)
            if globals.sourceport:
                while True:
                    result = validate_tests(generated_testfile, globals)
                    time.sleep(0.3)
                    if result == "success":
                        break
                    debug_testfile(result, testfile, globals)
            while True:
                result = run_test(generated_testfile, globals)
                if result == "success":
                    break
                debug_error(result, globals.testfiles, globals)
                run_dockerfile(globals)
                time.sleep(1)  # wait for docker to spin up

    typer.echo(typer.style("All tests complete. Ready to rumble. 💪", fg=typer.colors.GREEN))


if __name__ == "__main__":
    app()
