<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

<!-- PROJECT LOGO -->
<br />
  <a href="https://github.com/mattdeform/unreal_pycharm_debug">
    <img src="docs/resources/images/project_logo.png" alt="PyCharmLogo" width="30%">
  </a>

<h3 align="center">Unreal PyCharm Debug</h3>

  <p align="center">
    Development and Contributing Guidelines
    
</div>



<!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#project-dependencies">Project Dependencies</a></li>
    <li><a href="#continuous-integration">Continuous Integration</a></li>
    <li><a href="#tests">Tests</a></li>
    <li><a href="#linting-and-type-hinting">Linting and Type Hinting</a></li>
  </ol>
</details>

## Contributing
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature_name`).
3. Commit your Changes (`git commit -a -m "feat: a wonderful new feature"`).
4. Push to the Branch (`git push origin feature_name`).
5. Open a Pull Request.


## Project Dependencies
Project dependencies are available in the [requirements.in](requirements.in) file, which should be compiled with [pip-tools](https://github.com/jazzband/pip-tools). 

1. Install pip-tools: 
    ```sh
    pip install pip-tools
    ```
2. Dependencies can be added to:
    * [requirements.in](requirements.in): User requirements.
    * [requirements-dev.in](requirements-dev.in): Development requirements. 
    * [requirements-test.in](requirements-dev.in): Test requirements.
3. Compile the requirement files as needed:
    ```sh 
    pip-compile --output-file requirements.txt requirements.in requirements-dev.in requirements-test.in
    ``` 
4. Install dependencies:        
   * ```sh
        pip-sync
        ```
      </details>
    

<p align="right">(<a href="#readme-top">back to top</a>)</p> 

<!-- CI -->
## Continuous Integration
Continuous integration is set up with [GitHub Actions][github-actions-url], workflows can be found in the [.github/workflows](.github/workflows) directory. 

- [ci-main.yml](.github/workflows/ci-main.yml) runs tests, performs linting, formatting, and type hinting checks. It runs automatically on every push and pull request to main or can be triggered from the `Run workflow` button on the [actions menu](https://github.com/mattdeform/unreal_pycharm_debug/actions/workflows/ci-main.yml).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- TESTS -->
## Tests

Tests are written with [Pytest](https://docs.pytest.org/) and should adhere to the ["Arrange, Act, Assert" pattern](https://docs.pytest.org/en/stable/explanation/anatomy.html).

To run tests locally:
-   ```sh
    pytest
    ```

with coverage:
-   ```sh
    pytest --cov=plugin_src/PyCharmDebug/Content/Python
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Linting and Type Hinting
Static code analysis is performed with [Pylint](https://pypi.org/project/pylint/), formatting with [Black format](https://github.com/psf/black), and type hinting with [mypy](https://mypy.readthedocs.io/en/stable/).

To run pylint locally:

-   ```sh
    pylint --rcfile=.pylintrc plugin_src/PyCharmDebug/Content/Python/
    ```
    - A modified [.pylintrc](.pylintrc) file is provided with modifications to ignore Unreal import errors. Append to this file as needed.  

Black formater can be run locally with:

-   ```sh
    black plugin_src/PyCharmDebug/Content/Python/
    ```

Run [mypy](https://mypy.readthedocs.io/en/stable/) checks locally with:

-   ```sh
    mypy plugin_src/PyCharmDebug/Content/Python/
    ```
    - A modified [mypy.ini](mypy.ini) file is included with modifications to ignore Unreal import errors. Append to this file as needed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


[github-actions-url]: https://github.com/features/actions
