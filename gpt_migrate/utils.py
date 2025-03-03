import fnmatch
import glob
import os
import re
import shutil
from collections import Counter
from pathlib import Path

import typer
from config import (
    EXCLUDED_EXTENSIONS_SOURCE,
    EXTENSION_TO_LANGUAGE,
    INCLUDED_EXTENSIONS,
)
from yaspin import yaspin


def detect_language(source_directory):
    file_extensions = []

    # シンボリックリンクをたどるためにglobを使っています。
    for file in glob.glob(source_directory + "/**/*", recursive=True):
        if os.path.isfile(file):
            # ファイルの拡張子を取得します。
            ext = os.path.splitext(file)[1]

            if ext in EXCLUDED_EXTENSIONS_SOURCE:
                print(
                    f"""Excluded file: {0}
                    by EXCLUDED_EXTENSIONS_SOURCE={1}""".format(file, EXCLUDED_EXTENSIONS_SOURCE)
                )
                continue
            # ファイルの拡張子をリストに追加します。
            file_extensions.append(ext.replace(".", ""))

    extension_counts = Counter(file_extensions)
    print("ext most_common=", extension_counts.most_common(1))
    most_common_extension, _ = extension_counts.most_common(1)[0]

    # Determine the language based on the most common file extension
    language = EXTENSION_TO_LANGUAGE.get(most_common_extension, None)

    return language


def prompt_constructor(*args):
    prompt = ""
    for arg in args:
        with open(os.path.abspath(f"prompts/{arg}")) as file:
            prompt += file.read().strip()
    return prompt


def llm_run(prompt, waiting_message, success_message, globals):
    output = ""
    with yaspin(text=waiting_message, spinner="dots") as spinner:
        output = globals.ai.run(prompt)
        spinner.ok("✅ ")

    if success_message:
        success_text = typer.style(success_message, fg=typer.colors.GREEN)
        typer.echo(success_text)

    return output


def llm_write_file(prompt, target_path, waiting_message, success_message, globals):
    file_content = ""
    with yaspin(text=waiting_message, spinner="dots") as spinner:
        file_name, language, file_content = globals.ai.write_code(prompt)[0]
        spinner.ok("✅ ")

    if file_name == "INSTRUCTIONS:":
        return "INSTRUCTIONS:", "", file_content

    if file_name == "INSTRUCTIONS:":
        return "INSTRUCTIONS:", "", file_content

    targetdir = globals.targetdir
    if target_path:
        with open(os.path.join(targetdir, target_path), "w") as file:
            file.write(file_content)
    else:
        with open(os.path.join(targetdir, file_name), "w") as file:
            file.write(file_content)

    if success_message:
        success_text = typer.style(success_message, fg=typer.colors.GREEN)
        typer.echo(success_text)
    else:
        success_text = typer.style(f"Created {file_name} at {targetdir}", fg=typer.colors.GREEN)
        typer.echo(success_text)

    return file_name, language, file_content


def llm_write_files(prompt, target_path, waiting_message, success_message, globals):
    file_content = ""
    with yaspin(text=waiting_message, spinner="dots") as spinner:
        results = globals.ai.write_code(prompt)
        spinner.ok("✅ ")

    for result in results:
        file_name, language, file_content = result

        if target_path:
            with open(os.path.join(globals.targetdir, target_path), "w") as file:
                file.write(file_content)
        else:
            with open(os.path.join(globals.targetdir, file_name), "w") as file:
                file.write(file_content)

        if not success_message:
            success_text = typer.style(f"Created {file_name} at {globals.targetdir}", fg=typer.colors.GREEN)
            typer.echo(success_text)
    if success_message:
        success_text = typer.style(success_message, fg=typer.colors.GREEN)
        typer.echo(success_text)

    return results


def load_templates_from_directory(directory_path):
    templates = {}
    for filename in os.listdir(directory_path):
        with open(os.path.join(directory_path, filename)) as file:
            key = os.path.splitext(filename)[0]
            templates[key] = file.read()
    return templates


def parse_code_string(code_string):
    sections = code_string.split("---")

    pattern = re.compile(r"^(.+)\n```(.+?)\n(.*?)\n```", re.DOTALL)

    code_triples = []

    for section in sections:
        match = pattern.match(section)
        if match:
            filename, language, code = match.groups()
            code_triples.append((section.split("\n```")[0], language.strip(), code.strip()))

    return code_triples


def read_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(entry_path, gitignore_patterns):
    return any(fnmatch.fnmatch(entry_path, pattern) for pattern in gitignore_patterns)


def build_directory_structure(
    path=".",
    indent="",
    is_last=True,
    parent_prefix="",
    is_root=True,
    ignore_patterns=None,
):
    if ignore_patterns is None:
        ignore_patterns = []
    gitignore_patterns = read_gitignore(path) + [".gitignore", "*gpt_migrate/*"] if indent == "" else ["*gpt_migrate/*"]
    ignore_patterns = list(set(ignore_patterns + gitignore_patterns))
    base_name = os.path.basename(path)

    if not base_name:
        base_name = "."

    if indent == "":
        prefix = "|-- " if not is_root else ""
    elif is_last:
        prefix = parent_prefix + "└── "
    else:
        prefix = parent_prefix + "├── "

    if os.path.isdir(path):
        result = indent + prefix + base_name + "/\n" if not is_root else ""
    else:
        result = indent + prefix + base_name + "\n"

    if os.path.isdir(path):
        entries = os.listdir(path)
        for index, entry in enumerate(entries):
            entry_path = os.path.join(path, entry)
            new_parent_prefix = "    " if is_last else "│   "
            if not is_ignored(entry_path, gitignore_patterns):
                result += build_directory_structure(
                    entry_path,
                    indent + "    ",
                    index == len(entries) - 1,
                    parent_prefix + new_parent_prefix,
                    is_root=False,
                )

    return result


def copy_files(sourcedir, targetdir, excluded_files=[]):
    gitignore_patterns = read_gitignore(sourcedir) + [".gitignore"]
    for item in os.listdir(sourcedir):
        if os.path.isfile(os.path.join(sourcedir, item)):
            if item.endswith(INCLUDED_EXTENSIONS) and item not in excluded_files:
                if not is_ignored(item, gitignore_patterns):
                    os.makedirs(targetdir, exist_ok=True)
                    shutil.copy(os.path.join(sourcedir, item), targetdir)
                    # typer.echo(
                    #     typer.style(
                    #         f"Copied {item} from {sourcedir} to {targetdir}",
                    #         fg=typer.colors.GREEN,
                    #     )
                    # )
        else:
            copy_files(os.path.join(sourcedir, item), os.path.join(targetdir, item))


def construct_relevant_files(files):
    ret = ""
    for file in files:
        name = file[0]
        content = file[1]
        ret += name + ":\n\n" + "```\n" + content + "\n```\n\n"
    return ret


def file_exists_in_memory(filename):
    file = Path("memory/" + filename)
    return file.exists()


def convert_sigs_to_string(sigs):
    sig_string = ""
    for sig in sigs:
        sig_string += sig["signature"] + "\n" + sig["description"] + "\n\n"
    return sig_string


def write_to_memory(filename, content):
    with open("memory/" + filename, "a+") as file:
        for item in content:
            if item not in file.read().split("\n"):
                file.write(item + "\n")


def read_from_memory(filename):
    content = ""
    with open("memory/" + filename) as file:
        content = file.read()
    return content


def find_and_replace_file(filepath, find, replace):
    with open(filepath) as file:
        testfile_content = file.read()
    testfile_content = testfile_content.replace(find, replace)
    with open(filepath, "w") as file:
        file.write(testfile_content)
