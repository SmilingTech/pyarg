# Developers
> [!IMPORTANT]
> Before starting development on this repository, make sure you install all local development requirements.
```bash
$ python3 -m venv .env  # Create a virtual environment.
$ source .env/bin/activate  # Activate the virtual environment.
$ make setup-local-development  # Install all development requirements.
```

### Folder structure.
> [!WARNING]
> *This structure can be modified during the development of any project.*
```txt
.github/
    ᒪ workflows/
        ᒪ ...   # YAML files to be executed in GitHub workflows.
pyarg/  # Main library directory.
hooks/
    ᒪ ...   # Python scripts to be used as hooks in pre-commit.
.gitignore   # File with all files and folders to be ignored by Git.
.pre-commit-config.yaml   # Configuration file to set up local hooks for pre-commit.
.releaserc.json   # Plugins needed for generate the Release Notes.
DEVELOPERS.md   # Documentation for developers.
Makefile   # Used to define keywords to execute long commands.
pyproject.toml   # Main Python configuration file.
README.md   # Main project documentation.
```

### Conventional Commit Message.
All projects in this organizations must to use the conventional commit message format based on the following pattern:
```
^(feat|fix|docs|styles|refactor|test|chore|revert|ci|build|perf): .+$
```
|Type|Description|
|-|-|
|`feat`|Add a new functionality to the project.|
|`fix`|Fix a bug in the project.|
|`docs`|Changes in documentation. (README, comments, wikis, etc.)|
|`style`|Formatting, spacing, semicolons. Without changing the logic.|
|`refactor`|Rewriting/restructuring code without adding feature or fixing bug.|
|`test`|Add or fix tests. Without touching the main production code.|
|`chore`|Maintenance tasks: update dependencies, configs, build scripts.|
|`revert`|Revert a previous commit.|
|`ci`|Pipeline changes and CI/CD configurations. (GitHub Actions, etc.)|
|`build`|Changes in build system or external dependencies. (Dockerfile, Makefile, etc.)|
|`perf`|Code changes that improve performance without changing behavior.|
