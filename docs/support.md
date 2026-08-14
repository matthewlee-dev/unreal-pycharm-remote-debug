# Support & Roadmap

## Troubleshooting

Results show as a notification and in the Output Log.

| Notification | Fix                                                                                  |
| --- |--------------------------------------------------------------------------------------|
| No PyCharm location saved in Project Settings | Set **PyCharm Executable Location**.                                                 |
| PyCharm location ... does not exist | The saved path moved - re-pick it.                                                   |
| Found no `debug-eggs/pydevd-pycharm.egg` near ... | Point the path at PyCharm Professional; Community Edition is not supported.          |
| Failed to connect to PyCharm debug server on `host:port` | Start the Debug Server in PyCharm, and check **Debug Host**/**Debug Port** match it. |
| No debug host saved in Project Settings | Set **Debug Host**, `localhost` unless PyCharm is on another machine.                |
| Debug port ... is not a connectable port | Set **Debug Port** to the port of your Python Debug Server (1-65535).                |
| PythonScriptPlugin is unavailable | Enable **Python Script Plugin** under Edit -> Plugins.                               |

## Roadmap

See the [open issues](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues) for a full list of proposed features (and known issues).

## Report a bug or request a feature

* [Report Bug](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=bug&template=bug-report---.md)
* [Request Feature](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/issues/new?labels=enhancement&template=feature-request---.md)

## License

MIT, see [LICENSE](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/blob/main/LICENSE). No JetBrains code is redistributed.

## Contributing

See [CONTRIBUTING.md](https://github.com/matthewlee-dev/unreal-pycharm-remote-debug/blob/main/CONTRIBUTING.md).
