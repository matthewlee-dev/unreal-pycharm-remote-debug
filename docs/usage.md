# Usage

!!! warning "Step 1 is required"
    **Connect** fails until **PyCharm Executable Location** is set.

1. Edit -> Project Settings -> Plugins -> **PyCharm Remote Debug**. Set **PyCharm Executable Location** and **Debug Port** (default `5678`). Leave **Debug Host** as `localhost` unless PyCharm is on another machine.

    ![PyCharm Remote Debug entry in Project Settings' Plugins list](resources/images/rename_button.png)

    | Platform | PyCharm Executable Location |
    | --- | --- |
    | Windows | `C:\Program Files\JetBrains\PyCharm 2025.1\bin\pycharm64.exe` |
    | macOS | `/Applications/PyCharm.app` |
    | Linux | `/opt/pycharm-2025.1/bin/pycharm.sh` |

2. In PyCharm, create a Python Debug Server named ___Unreal___ on that port, and start it.
3. Level editor: PyCharm -> Connect.

Breakpoints now hit, and can be set before or after connecting. PyCharm ->
Disconnect when done.

!!! tip
    Debugging a different machine? See [Remote Setup](remote-setup.md).

## Troubleshooting

Connect and Disconnect show the result as a notification, and in the Output Log.
Failures link to the settings panel.

| Notification | Fix                                                                                  |
| --- |--------------------------------------------------------------------------------------|
| No PyCharm location saved in Project Settings | Set **PyCharm Executable Location** (step 1).                                        |
| PyCharm location ... does not exist | The saved path moved - re-pick it.                                                   |
| Found no `debug-eggs/pydevd-pycharm.egg` near ... | Point the path at PyCharm Professional; Community Edition is not supported.          |
| Failed to connect to PyCharm debug server on `host:port` | Start the Debug Server in PyCharm, and check **Debug Host**/**Debug Port** match it. |
| No debug host saved in Project Settings | Set **Debug Host**, `localhost` unless PyCharm is on another machine.                |
| Debug port ... is not a connectable port | Set **Debug Port** to the port of your Python Debug Server (1-65535).                |
| PythonScriptPlugin is unavailable | Enable **Python Script Plugin** under Edit -> Plugins.                               |
