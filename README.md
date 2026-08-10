<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![CI](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/actions/workflows/ci-main.yml/badge.svg)](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/actions/workflows/ci-main.yml)
[![pytest][pytest-shield]][pytest-url]
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)


<!-- PROJECT LOGO -->
<br />
  <a href="https://github.com/matthewlee-dev/unreal-pycharm-remote-debug">
    <img src="docs/resources/images/project_logo.png" alt="Unreal" width="50%">
  </a>

[![Python][python_3-shield]][python-url]
[![Unreal][unreal_5-shield]][unreal-url]

<h3 align="center">Unreal PyCharm Remote Debug</h3>
  An Unreal Engine plugin for connecting to a PyCharm debugger.
  <br />
  <p align="center">
    <a href="https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#usage">Usage</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project
> __This is NOT an official JetBrains or Epic Games plugin.__

<div align="center">

<img src="docs/resources/images/screenshot.png" alt="Unreal" width="900">

</div>
    
<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* [Unreal Engine 5](https://www.unrealengine.com) - Windows, macOS or Linux editor.
* [PyCharm Professional](https://www.jetbrains.com/pycharm/buy/) - the debug egg does not ship with Community Edition.
* Visual Studio (Windows) or Xcode (macOS) - the editor compiles the plugin on first open.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Installation

1. Download the zip for your engine version from [Releases](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/releases).
2. Extract into `YourProject/Plugins/`.
3. Open the project and answer **Yes** to the rebuild prompt.
4. Enable under Edit -> Plugins, restart if prompted.

A **PyCharm** menu appears in the level editor.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
### Usage

1. Edit -> Project Settings -> Plugins -> **PyCharm Remote Debug**. Set **PyCharm Executable Location** and **Debug Port** (default `5678`). Leave **Debug Host** as `localhost` unless PyCharm is on another machine.

    | Platform | PyCharm Executable Location |
    | --- | --- |
    | Windows | `C:\Program Files\JetBrains\PyCharm 2025.1\bin\pycharm64.exe` |
    | macOS | `/Applications/PyCharm.app` |
    | Linux | `/opt/pycharm-2025.1/bin/pycharm.sh` |

2. In PyCharm, create a Python Debug Server named ___Unreal___ on that port, and start it.
3. Level editor: PyCharm -> Connect. <i>The editor freezes until PyCharm attaches</i>.
4. In PyCharm, click "Resume Program" or press F9.

Breakpoints now hit. PyCharm -> Disconnect when done; connect and disconnect cycle freely.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Contributing
If you have a suggestion that would make this better, please open an issue from the [request a feature](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=enhancement&template=feature-request---.md) or [report a bug](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=bug&template=bug-report---.md) pages.

Development and contribution guidelines can be found on the [CONTRIBUTING.md](CONTRIBUTING.md) page

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

MIT, see [LICENSE](LICENSE). No JetBrains code is redistributed - the debug egg is read from your own PyCharm install at runtime.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Please reach out via the [request a feature](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=enhancement&template=feature-request---.md) or [report a bug](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=bug&template=bug-report---.md) pages.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments
* Project template by [matthewlee-dev](https://github.com/matthewlee-dev/MayaPythonProjectTemplate).
* [deform.dev](https://deform.dev)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

<!-- Python -->
[python-shield]: https://img.shields.io/badge/python-3670A0?logo=python&logoColor=ffdd54
[python_2-shield]: https://img.shields.io/badge/Python-2.X-grey?logo=python&logoColor=ffdd54&labelColor=%233670A0
[python_3-shield]: https://img.shields.io/badge/Python-3.X-grey?logo=python&logoColor=ffdd54&labelColor=%233670A0
[python-url]: https://python.org/
[pytest-shield]: https://img.shields.io/badge/tests-pytest-%230A9EDC
[pytest-url]: https://docs.pytest.org/
[unreal_5-shield]: https://img.shields.io/badge/Unreal%20Engine-5.x-grey?logo=unrealengine&labelColor=%230E1128
[unreal-url]: https://www.unrealengine.com/en-US
