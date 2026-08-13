// Copyright (c) 2026 Matthew Lee

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "PyCharmRemoteDebugNotifications.generated.h"

/**
 * Editor feedback for the Connect/Disconnect menu actions, which otherwise
 * report failures to the Output Log only.
 *
 * BlueprintCallable is what exports these to Python - PythonScriptPlugin only
 * wraps Blueprint-exposed functions.
 */
UCLASS()
class PYCHARMREMOTEDEBUG_API UPyCharmRemoteDebugNotifications : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Raise a toast in the editor. Errors also carry a link to the settings panel. */
	UFUNCTION(BlueprintCallable, Category = "PyCharmRemoteDebug")
	static void ShowNotification(const FString& Message, bool bIsError = false);

	/** Open Project Settings > Plugins > PyCharm Remote Debug. */
	UFUNCTION(BlueprintCallable, Category = "PyCharmRemoteDebug")
	static void OpenSettings();
};
