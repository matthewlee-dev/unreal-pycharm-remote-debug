# Installation

## Dependencies

**Python Script Plugin** (`PythonScriptPlugin`).

## From Fab (recommended)

The plugin is distributed on the [Fab marketplace](https://www.fab.com). Fab
builds the binaries for your engine version, so no local compiler is needed.

1. Add the plugin to your library from the [Fab listing page](https://www.fab.com).
2. In the Epic Games Launcher, open your project and use **Add to Project** on the listing.
3. Enable under Edit -> Plugins, restart if prompted.

![Enabling the plugin in the Unreal Plugins panel](resources/images/plugin_enable.png)

A **PyCharm** menu appears in the level editor once it's enabled.

![The PyCharm menu in the level editor toolbar](resources/images/toolbar_button.png)

## From a manual download

Prefer not to use Fab? A source zip is also published on
[GitHub Releases](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/releases).
This route ships source only, so the editor compiles it on first open - you'll
need Visual Studio (Windows) or Xcode (macOS) installed.

1. Download the zip for your engine version from [Releases](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/releases).
2. Extract into `YourProject/Plugins/`.
3. Open the project and answer **Yes** to the rebuild prompt.
4. Enable under Edit -> Plugins, restart if prompted.

## Next

Set **PyCharm Executable Location** before connecting - see [Usage](usage.md).
