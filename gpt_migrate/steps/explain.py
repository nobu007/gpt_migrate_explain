import json
import os

import typer
from config import (
    ADD_DOCKER_REQUIREMENTS,
    EXCLUDED_FILES,
    GET_EXTERNAL_DEPS_EXPLAIN,
    GET_FUNCTION_SIGNATURES_EXPLAIN,
    GET_INTERNAL_DEPS_EXPLAIN,
    GUIDELINES,
    HIERARCHY,
    REFINE_DOCKERFILE,
    SINGLEFILE,
    WRITE_CODE,
)
from utils import (
    build_directory_structure,
    copy_files,
    extract_json_from_response,
    file_exists_in_memory,
    get_near_source_directory_structure,
    llm_run,
    llm_write_file,
    prompt_constructor,
    read_from_memory,
    write_file_explain,
    write_to_memory,
)


def get_function_signatures_explain(targetfiles: list[str], globals):
    """Get the function signatures and a one-sentence summary for each function"""
    all_sigs = []

    for targetfile in targetfiles:
        sigs_file_name = targetfile + "_sigs.json"

        if file_exists_in_memory(sigs_file_name):
            with open(
                os.path.join("gpt_migrate_explain/gpt_migrate/memory", sigs_file_name),
            ) as f:
                sigs = json.load(f)
            all_sigs.extend(sigs)

        else:
            function_signatures_template = prompt_constructor(HIERARCHY, GUIDELINES, GET_FUNCTION_SIGNATURES_EXPLAIN)

            sourcefile_content = ""
            print("targetfile=" + targetfile)
            with open(os.path.join(globals.sourcedir, targetfile)) as file:
                sourcefile_content = file.read()

            prompt = function_signatures_template.format(
                targetlang=globals.targetlang,
                sourcelang=globals.sourcelang,
                sourcefile_content=sourcefile_content,
            )

            try:
                sigs = json.loads(
                    extract_json_from_response(
                        llm_run(
                            prompt,
                            waiting_message=f"Parsing function signatures for {targetfile}...",
                            success_message=None,
                            globals=globals,
                        )
                    )
                )
                all_sigs.extend(sigs)

                memory_dir = "gpt_migrate_explain/gpt_migrate/memory"
                sigs_file_path = os.path.join(memory_dir, sigs_file_name)
                os.makedirs(os.path.dirname(sigs_file_path), exist_ok=True)
                with open(
                    sigs_file_path,
                    "w",
                ) as f:
                    json.dump(sigs, f)
            except json.decoder.JSONDecodeError:
                pass

    return all_sigs


def get_dependencies_explain(sourcefile, globals):
    """Get external and internal dependencies of source file"""

    external_deps_prompt_template = prompt_constructor(HIERARCHY, GUIDELINES, GET_EXTERNAL_DEPS_EXPLAIN)
    internal_deps_prompt_template = prompt_constructor(HIERARCHY, GUIDELINES, GET_INTERNAL_DEPS_EXPLAIN)

    sourcefile_content = ""
    with open(os.path.join(globals.sourcedir, sourcefile)) as file:
        sourcefile_content = file.read()

    prompt = external_deps_prompt_template.format(
        targetlang=globals.targetlang,
        sourcelang=globals.sourcelang,
        sourcefile_content=sourcefile_content,
    )

    external_dependencies = llm_run(
        prompt,
        waiting_message=f"Identifying external dependencies for {sourcefile}...",
        success_message=None,
        globals=globals,
    )

    external_deps_list = external_dependencies.split(",") if external_dependencies != "NONE" else []
    write_to_memory("external_dependencies", external_deps_list)

    near_source_directory_structure = get_near_source_directory_structure(
        globals.source_directory_structure, sourcefile
    )
    prompt = internal_deps_prompt_template.format(
        targetlang=globals.targetlang,
        sourcelang=globals.sourcelang,
        sourcefile=sourcefile,
        sourcefile_content=sourcefile_content,
        source_directory_structure=near_source_directory_structure,
    )

    internal_dependencies = llm_run(
        prompt,
        waiting_message=f"Identifying internal dependencies for {sourcefile}...",
        success_message=None,
        globals=globals,
    )
    print("internal_dependencies=", internal_dependencies)

    # Sanity checking internal dependencies to avoid infinite loops
    if sourcefile in internal_dependencies:
        typer.echo(
            typer.style(
                f"Warning: {sourcefile} seems to depend on itself. Automatically removing {sourcefile} from the list of internal dependencies.",
                fg=typer.colors.YELLOW,
            )
        )
        internal_dependencies = internal_dependencies.replace(sourcefile, "")

    internal_deps_list = (
        [dep for dep in internal_dependencies.split(",") if dep] if internal_dependencies != "NONE" else []
    )

    write_to_memory("internal_dependencies", internal_deps_list)

    return internal_deps_list, external_deps_list


def write_explain(sourcefile_relative_path, external_deps_list, deps_per_file, globals) -> str:
    """Write explain file"""

    # sigs = (
    #     get_function_signatures_explain(deps_per_file, globals) if deps_per_file else []
    # )

    # write_explain_template = prompt_constructor(
    #     HIERARCHY, GUIDELINES, WRITE_EXPLAIN, SINGLEFILE_EXPLAIN
    # )
    # write_explain_template = prompt_constructor(HIERARCHY, GUIDELINES, WRITE_EXPLAIN)
    sourcefile_abs_path = os.path.join(globals.sourcedir, sourcefile_relative_path)
    sourcefile_content = ""
    with open(sourcefile_abs_path) as file:
        sourcefile_content = file.read()

    globals.sourcefile_content = sourcefile_content

    # prompt = write_explain_template.format(
    #     targetlang=globals.targetlang,
    #     targetlang_function_signatures=convert_sigs_to_string(sigs),
    #     sourcelang=globals.sourcelang,
    #     sourcefile=sourcefile,
    #     sourcefile_content=sourcefile_content,
    #     external_deps=",".join(external_deps_list),
    #     source_directory_structure=globals.source_directory_structure,
    #     explain_directory_structure=build_directory_structure(globals.explaindir),
    #     guidelines=globals.guidelines,
    # )

    # build prompt and predict by llm

    # split sourcefile_content for llm input
    sourcefile_content_list = globals.ai.split_sourcefile_content(sourcefile_abs_path, sourcefile_content)

    # call llm
    splitted_explainfile_content_list = []
    for sourcefile_content in sourcefile_content_list:
        response_list = globals.ai.write_explain_llm(sourcefile_content, globals)
        for response in response_list:
            splitted_explainfile_content_list.append(response)

    # set explainfile_content
    globals.explainfile_content = "\n\n\n".join(splitted_explainfile_content_list)
    explainfile_relative_path = sourcefile_relative_path.replace(globals.sourcedir, globals.explaindir)

    return write_file_explain(
        explainfile_relative_path,
        globals=globals,
    )[0]


def add_env_files_explain(globals):
    """Copy all files recursively with included extensions from the source directory to the target directory in the same relative structure"""

    copy_files(globals.sourcedir, globals.targetdir, excluded_files=EXCLUDED_FILES)

    """ Add files required from the Dockerfile """

    add_docker_requirements_template = prompt_constructor(
        HIERARCHY, GUIDELINES, WRITE_CODE, ADD_DOCKER_REQUIREMENTS, SINGLEFILE
    )

    dockerfile_content = ""
    dockerfile_path = os.path.join(globals.targetdir, "Dockerfile")
    if not os.path.isfile(dockerfile_path):
        return
    with open(dockerfile_path) as file:
        dockerfile_content = file.read()

    external_deps = read_from_memory("external_dependencies")

    prompt = add_docker_requirements_template.format(
        dockerfile_content=dockerfile_content,
        external_deps=external_deps,
        target_directory_structure=build_directory_structure(globals.targetdir),
        targetlang=globals.targetlang,
        guidelines=globals.guidelines,
    )

    external_deps_name, _, external_deps_content = llm_write_file(
        prompt,
        target_path=None,
        waiting_message="Creating dependencies file required for the Docker environment...",
        success_message=None,
        globals=globals,
        targetdir=globals.explaindir,
    )

    """ Refine Dockerfile """

    refine_dockerfile_template = prompt_constructor(HIERARCHY, GUIDELINES, WRITE_CODE, REFINE_DOCKERFILE, SINGLEFILE)
    prompt = refine_dockerfile_template.format(
        dockerfile_content=dockerfile_content,
        target_directory_structure=build_directory_structure(globals.targetdir),
        external_deps_name=external_deps_name,
        external_deps_content=external_deps_content,
        guidelines=globals.guidelines,
    )

    llm_write_file(
        prompt,
        target_path="Dockerfile",
        waiting_message="Refining Dockerfile based on dependencies required for the Docker environment...",
        success_message="Refined Dockerfile with dependencies required for the Docker environment.",
        globals=globals,
        targetdir=globals.explaindir,
    )
