<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

<!-- PROJECT LOGO -->
<br />
  <a href="https://github.com/matthewlee-dev/unreal_pycharm_remote_debug">
    <img src="docs/resources/images/project_logo.png" alt="PyCharmLogo" width="30%">
  </a>

<h3 align="center">Unreal PyCharm Remote Debug</h3>

  <p align="center">
    Development and Contributing Guidelines
    
</div>



<!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#project-layout">Project Layout</a></li>
    <li><a href="#project-dependencies">Project Dependencies</a></li>
    <li><a href="#building-the-plugin">Building the Plugin</a></li>
    <li><a href="#continuous-integration">Continuous Integration</a></li>
    <li><a href="#tests">Tests</a></li>
    <li><a href="#linting-and-type-hinting">Linting and Type Hinting</a></li>
    <li><a href="#releasing">Releasing</a></li>
  </ol>
</details>

## Contributing
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature_name`).
3. Commit your Changes (`git commit -a -m "feat: a wonderful new feature"`).
4. Push to the Branch (`git push origin feature_name`).
5. Open a Pull Request.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Project Layout

```
plugin_src/PyCharmRemoteDebug/
  Source/                            editor module: menu + Project Settings
  Content/Python/pycharmremotedebug/ bridge.py, session.py - all pydevd calls
scripts/package_plugin.py            builds the release zip
tests/unit/                          pytest suite (CI)
tests/uat/                           run by hand in the editor
```

`settrace()` must run inside Unreal's embedded interpreter, hence the split.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Project Dependencies

Dependencies live in [pyproject.toml](pyproject.toml) and are pinned by
[uv.lock](uv.lock). The plugin itself ships none - it uses the standard library,
the `unreal` module and pydevd from your PyCharm install - so the groups are
tooling only.

1. Install [uv](https://docs.astral.sh/uv/).
2. Create the environment (reads [.python-version](.python-version) and the lock):
    ```sh
    uv sync --group dev --group test
    ```
3. Add or change a dependency in `pyproject.toml`, then re-lock:
    ```sh
    uv lock
    ```

Commit `uv.lock` with the change. Commands below use `uv run`, which syncs the
environment first, so an explicit `uv sync` is only needed to prepare an IDE.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- BUILDING -->
## Building the Plugin

Python changes need only an editor restart. C++ changes need a build - the editor
rebuilds a plugin only when its binary is missing or engine-incompatible.

Point a test project at this repo:

```jsonc
"Plugins": [ { "Name": "PyCharmRemoteDebug", "Enabled": true } ],
"AdditionalPluginDirectories": [ "<path to>/unreal_pycharm_remote_debug/plugin_src" ]
```

Build with the editor closed:

```sh
# macOS
<Engine>/Build/BatchFiles/Mac/Build.sh <Project>Editor Mac Development \
  -Project="<path>/<Project>.uproject" -Progress
# Windows
<Engine>\Build\BatchFiles\Build.bat <Project>Editor Win64 Development ^
  -Project="<path>\<Project>.uproject" -Progress
```

* Target is `<Project>Editor`, not `UnrealEditor`.
* Adding `-TargetType=Editor` to that fails with `ActionGraphInvalid`.
* `UPROPERTY` names reach Python snake-cased: `PyCharmPath` -> `py_charm_path`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CI -->
## Continuous Integration
Continuous integration is set up with [GitHub Actions][github-actions-url], workflows can be found in the [.github/workflows](.github/workflows) directory. 

- [ci-main.yml](.github/workflows/ci-main.yml) runs tests, performs linting, formatting, and type hinting checks. It runs automatically on every push and pull request to main or can be triggered from the `Run workflow` button on the [actions menu](https://github.com/matthewlee-dev/unreal_pycharm_remote_debug/actions/workflows/ci-main.yml).
- [release.yml](.github/workflows/release.yml) packages a release, see [Releasing](#releasing). Manual trigger only.

Neither compiles the plugin - hosted runners have no Unreal. Verify C++ locally.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- TESTS -->
## Tests

Tests are written with [Pytest](https://docs.pytest.org/) and should adhere to the ["Arrange, Act, Assert" pattern](https://docs.pytest.org/en/stable/explanation/anatomy.html).

To run tests locally:
-   ```sh
    uv run --group test pytest
    ```

with coverage:
-   ```sh
    uv run --group test pytest --cov=plugin_src/PyCharmRemoteDebug/Content/Python
    ```

`tests/unit` is what CI runs; `unreal` is mocked. `tests/uat` is run by hand from
the editor's Python console against a live session.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Linting and Type Hinting
Static code analysis is performed with [Pylint](https://pypi.org/project/pylint/), formatting with [Black format](https://github.com/psf/black), and type hinting with [mypy](https://mypy.readthedocs.io/en/stable/).

To run pylint locally:

-   ```sh
    uv run --group dev pylint --rcfile=.pylintrc plugin_src/PyCharmRemoteDebug/Content/Python/ scripts/
    ```
    - A modified [.pylintrc](.pylintrc) file is provided with modifications to ignore Unreal import errors. Append to this file as needed.  

Black formater can be run locally with:

-   ```sh
    uv run --group dev black plugin_src/PyCharmRemoteDebug/Content/Python/ scripts/
    ```

Run [mypy](https://mypy.readthedocs.io/en/stable/) checks locally with:

-   ```sh
    uv run --group dev mypy plugin_src/PyCharmRemoteDebug/Content/Python/ scripts/
    ```
    - A modified [mypy.ini](mypy.ini) file is included with modifications to ignore Unreal import errors. Append to this file as needed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- RELEASING -->
## Releasing

Run [release.yml](.github/workflows/release.yml) from the `Run workflow` button:

| input | example | meaning |
| --- | --- | --- |
| `version` | `1.2.0` | must be `major.minor.patch` |
| `engine_versions` | `5.6,5.7` | one zip per entry |
| `draft` | `true` | create the release as a draft |

Tests and static analysis run first, then `PyCharmRemoteDebug-<version>-UE<engine>.zip`
is attached to a `v<version>` release. Each zip is the plugin folder at the archive
root, build output stripped - the layout Fab expects, since Fab distributes source
and Epic compiles it. Only the staged `.uplugin` is stamped, never the repo's.

Same artifacts locally:

```sh
uv run scripts/package_plugin.py --plugin-dir plugin_src/PyCharmRemoteDebug \
  --output-dir dist --version 1.2.0 --engine-versions "5.7"
```

> Nothing verifies the plugin compiles on the engine versions you list. Build
> against them locally first.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


[github-actions-url]: https://github.com/features/actions
