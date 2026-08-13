# Usage

1. Edit -> Project Settings -> Plugins -> **PyCharm Remote Debug**. Set **PyCharm Executable Location** and **Debug Port** (default `5678`). Leave **Debug Host** as `localhost` unless PyCharm is on another machine.

    ![PyCharm Remote Debug entry in Project Settings' Plugins list](resources/images/rename_button.png)

    | Platform | PyCharm Executable Location |
    | --- | --- |
    | Windows | `C:\Program Files\JetBrains\PyCharm 2025.1\bin\pycharm64.exe` |
    | macOS | `/Applications/PyCharm.app` |
    | Linux | `/opt/pycharm-2025.1/bin/pycharm.sh` |

2. In PyCharm, create a Python Debug Server named ___Unreal___ on that port, and start it.
3. Level editor: PyCharm -> Connect. <i>The editor freezes until PyCharm attaches</i>.
4. In PyCharm, click "Resume Program" or press F9.

Breakpoints now hit. PyCharm -> Disconnect when done; connect and disconnect cycle freely.

!!! tip
    Debugging a different machine? See [Remote Setup](remote-setup.md).
