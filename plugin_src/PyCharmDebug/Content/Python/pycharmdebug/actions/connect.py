import sys

import unreal

from ..utils import (
    get_debug_egg,
    get_debug_port,
)


ACTION_NAME = "start_debugger"
ACTION_LABEL = "Connect"
ICON_STYLE = "EditorStyle"
ICON_NAME = "Sequencer.IconKeyBreak"
HOST = "localhost"


@unreal.uclass()
class PyCharmDebugConnect(unreal.ToolMenuEntryScript):
    """Menu action to connect to a PyCharm debugger from within the
    level editor"""

    def __init__(self) -> None:
        super().__init__()
        self.data.name = ACTION_NAME
        self.data.label = ACTION_LABEL
        self.data.advanced.entry_type = unreal.MultiBlockType.TOOL_BAR_BUTTON
        self.data.icon = unreal.ScriptSlateIcon(ICON_STYLE, ICON_NAME)

    @unreal.ufunction(override=True)
    def execute(
        self, context: unreal.ToolMenuContext  # pylint: disable=(unused-argument)
    ) -> None:
        """Connect to the PyCharm debugger, via the port specified in
        Resources/config.json

        Args:
            context (unreal.ToolMenuContext): ToolMenuContext context object
        """
        dbg_egg = get_debug_egg()
        if dbg_egg is None:
            return
        sys.path.append(dbg_egg)

        try:
            import pydevd_pycharm
        except ImportError:
            unreal.log_error("Failed to import pydevd_pycharm")
            return
        try:
            pydevd_pycharm.settrace(
                HOST,
                port=get_debug_port(),
                stdoutToServer=True,
                stderrToServer=True,
            )
        except TypeError:  # new versions of pydevd_pycharm moved to snake case
            pydevd_pycharm.settrace(
                HOST,
                port=get_debug_port(),
                stdout_to_server=True,
                stderr_to_server=True,
            )
        unreal.log("Connected to PyCharm debugger")
