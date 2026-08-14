// Copyright (c) 2026 Matthew Lee

#include "PyCharmRemoteDebugModule.h"

#include "Framework/Commands/UIAction.h"
#include "IPythonScriptPlugin.h"
#include "Modules/ModuleManager.h"
#include "PyCharmRemoteDebugNotifications.h"
#include "Textures/SlateIcon.h"
#include "ToolMenus.h"

#define LOCTEXT_NAMESPACE "FPyCharmRemoteDebugModule"

DEFINE_LOG_CATEGORY(LogPyCharmRemoteDebug);

void FPyCharmRemoteDebugModule::StartupModule()
{
	// UToolMenus is not ready this early in editor startup
	UToolMenus::RegisterStartupCallback(
		FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FPyCharmRemoteDebugModule::RegisterMenus));
}

void FPyCharmRemoteDebugModule::ShutdownModule()
{
	UToolMenus::UnRegisterStartupCallback(this);
	UToolMenus::UnregisterOwner(this);
}

void FPyCharmRemoteDebugModule::RegisterMenus()
{
	// owner-scoped so ShutdownModule() removes only our entries
	FToolMenuOwnerScoped OwnerScoped(this);

	UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu(TEXT("LevelEditor.MainMenu"));
	if (!MainMenu)
	{
		UE_LOG(LogPyCharmRemoteDebug, Error, TEXT("Failed to find LevelEditor.MainMenu, PyCharm menu not installed"));
		return;
	}

	FToolMenuSection& Section = MainMenu->FindOrAddSection(TEXT("Python"));

	Section.AddSubMenu(
		TEXT("dbg_menu"),
		LOCTEXT("PyCharmMenuLabel", "PyCharm"),
		LOCTEXT("PyCharmMenuTooltip", "PyCharm debugger connection"),
		FNewToolMenuDelegate::CreateRaw(this, &FPyCharmRemoteDebugModule::PopulatePyCharmMenu));
}

void FPyCharmRemoteDebugModule::PopulatePyCharmMenu(UToolMenu* Menu)
{
	FToolMenuSection& Section = Menu->FindOrAddSection(TEXT("Items"));

	Section.AddMenuEntry(
		TEXT("start_debugger"),
		LOCTEXT("ConnectLabel", "Connect"),
		LOCTEXT("ConnectTooltip", "Connect to a PyCharm debug server using the host/port/PyCharm location from Project Settings"),
		FSlateIcon(TEXT("EditorStyle"), TEXT("Sequencer.IconKeyBreak")),
		FUIAction(FExecuteAction::CreateRaw(this, &FPyCharmRemoteDebugModule::OnConnectClicked)));

	Section.AddMenuEntry(
		TEXT("stop_debugger"),
		LOCTEXT("DisconnectLabel", "Disconnect"),
		LOCTEXT("DisconnectTooltip", "Disconnect from the PyCharm debug server"),
		FSlateIcon(TEXT("EditorStyle"), TEXT("Sequencer.IconKeyAuto")),
		FUIAction(FExecuteAction::CreateRaw(this, &FPyCharmRemoteDebugModule::OnDisconnectClicked)));
}

void FPyCharmRemoteDebugModule::OnConnectClicked()
{
	ExecuteBridgeCommand(TEXT("from pycharmremotedebug import bridge; bridge.connect()"));
}

void FPyCharmRemoteDebugModule::OnDisconnectClicked()
{
	ExecuteBridgeCommand(TEXT("from pycharmremotedebug import bridge; bridge.disconnect()"));
}

void FPyCharmRemoteDebugModule::ExecuteBridgeCommand(const TCHAR* PythonCommand)
{
	IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
	if (!PythonPlugin)
	{
		const FString Message = TEXT("PythonScriptPlugin is unavailable, enable it in Edit > Plugins");
		UE_LOG(LogPyCharmRemoteDebug, Error, TEXT("%s"), *Message);
		UPyCharmRemoteDebugNotifications::ShowNotification(Message, /*bIsError=*/true);
		return;
	}

	FPythonCommandEx Command;
	Command.Command = PythonCommand;
	Command.ExecutionMode = EPythonCommandExecutionMode::ExecuteStatement;

	// the bridge reports its own failures; this catches it not running at all
	if (!PythonPlugin->ExecPythonCommandEx(Command))
	{
		const FString Message = TEXT("PyCharm Remote Debug command failed, see the Output Log");
		UE_LOG(LogPyCharmRemoteDebug, Error, TEXT("%s"), *Message);
		UPyCharmRemoteDebugNotifications::ShowNotification(Message, /*bIsError=*/true);
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FPyCharmRemoteDebugModule, PyCharmRemoteDebug)