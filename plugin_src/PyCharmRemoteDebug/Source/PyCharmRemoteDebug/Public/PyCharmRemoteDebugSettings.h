// Copyright (c) 2026 Matthew Lee

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "PyCharmRemoteDebugSettings.generated.h"

/**
 * Settings for PyCharm Remote Debug.
 */
UCLASS(Config = EditorPerProjectUserSettings, BlueprintType,
	meta = (DisplayName = "PyCharm Remote Debug"))
class PYCHARMREMOTEDEBUG_API UPyCharmRemoteDebugSettings : public UDeveloperSettings
{
	GENERATED_BODY()

	// Notes live inside the class: UHT folds comments above a UCLASS/UPROPERTY
	// into the Project Settings tooltip.
	//
	// BlueprintType is what gets this class a Python wrapper - PythonScriptPlugin
	// only exports Blueprint types (PyGenUtil::ShouldExportClass). Without it
	// unreal.PyCharmRemoteDebugSettings does not exist. EditAnywhere is enough for
	// the properties; get_editor_property() reads those off CPF_Edit.
	//
	// PyCharmPath sets no FilePathFilter: it must accept .exe, .sh and an
	// extensionless binary, and on macOS any filter makes the picker descend into
	// PyCharm.app rather than offer the bundle.
	//
	// Renaming a property renames it in Python: PyCharmPath -> "py_charm_path".
	// Keep PYCHARM_PATH_PROPERTY in bridge.py in step.

public:
	UPyCharmRemoteDebugSettings();

	// PyCharm executable: bin/pycharm64.exe on Windows, Contents/MacOS/pycharm
	// on macOS, bin/pycharm.sh on Linux. On macOS you can also point this at
	// PyCharm.app itself.
	UPROPERTY(Config, EditAnywhere, Category = "PyCharmRemoteDebug",
		meta = (DisplayName = "PyCharm Executable Location"))
	FFilePath PyCharmPath;

	// Host where the PyCharm debug server listens. Only change from
	// "localhost" when the editor and PyCharm run on different machines.
	UPROPERTY(Config, EditAnywhere, Category = "PyCharmRemoteDebug",
		meta = (DisplayName = "Debug Host"))
	FString Host = TEXT("localhost");

	// Must match the port of the "Unreal" Python Debug Server configured in PyCharm.
	UPROPERTY(Config, EditAnywhere, Category = "PyCharmRemoteDebug",
		meta = (DisplayName = "Debug Port", ClampMin = "0", ClampMax = "65535"))
	int32 PortNumber = 5678;

	virtual FName GetContainerName() const override { return "Project"; }
	virtual FName GetCategoryName() const override { return "Plugins"; }
};