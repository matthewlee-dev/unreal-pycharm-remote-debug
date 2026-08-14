# Remote Setup

Start the Python Debug Server on the PyCharm machine *before* connecting from Unreal.

* PyCharm machine: allow the debug port through the firewall.
* Unreal machine: set **Debug Host** to the PyCharm machine's LAN IP, and **PyCharm Executable Location** to a local PyCharm Professional install.
* In PyCharm, Debug Server config -> **Path mappings**: map your tool's local source folder to its path on the Unreal machine.

| Local (PyCharm) | Remote (Unreal) |
| --- | --- |
| `.../MyProject/Content/Python/my_awesome_tool` | `C:\...\MyProject\Content\Python\my_awesome_tool` (Windows) or `/.../MyProject/Content/Python/my_awesome_tool` (macOS/Linux) |
