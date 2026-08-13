// Copyright (c) 2026 Matthew Lee

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleInterface.h"

class UToolMenu;

DECLARE_LOG_CATEGORY_EXTERN(LogPyCharmRemoteDebug, Log, All);

/**
 * Editor module: registers the "PyCharm" menu and routes Connect/Disconnect to
 * pycharmremotedebug/bridge.py. settrace() must run inside Unreal's embedded
 * interpreter, so this module never talks to pydevd directly.
 */
class FPyCharmRemoteDebugModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	// deferred until UToolMenus announces startup
	void RegisterMenus();
	void PopulatePyCharmMenu(UToolMenu* Menu);

	void OnConnectClicked();
	void OnDisconnectClicked();

	// the bridge reads settings itself via reflection, so no values are
	// interpolated into the command string - no path-escaping bugs
	void ExecuteBridgeCommand(const TCHAR* PythonCommand);
};