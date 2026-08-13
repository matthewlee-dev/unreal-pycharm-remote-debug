// Copyright (c) 2026 Matthew Lee

#include "PyCharmRemoteDebugNotifications.h"

#include "Framework/Notifications/NotificationManager.h"
#include "ISettingsModule.h"
#include "Modules/ModuleManager.h"
#include "PyCharmRemoteDebugModule.h"
#include "PyCharmRemoteDebugSettings.h"
#include "Widgets/Notifications/SNotificationItem.h"

#define LOCTEXT_NAMESPACE "PyCharmRemoteDebugNotifications"

namespace
{
	// failures need long enough to read a path out of
	constexpr float SuccessDurationSeconds = 4.0f;
	constexpr float ErrorDurationSeconds = 12.0f;
}

void UPyCharmRemoteDebugNotifications::ShowNotification(const FString& Message, bool bIsError)
{
	FNotificationInfo Info(FText::FromString(Message));
	Info.bFireAndForget = true;
	Info.bUseSuccessFailIcons = true;
	Info.ExpireDuration = bIsError ? ErrorDurationSeconds : SuccessDurationSeconds;

	if (bIsError)
	{
		// failures are near always a wrong or missing setting
		Info.Hyperlink = FSimpleDelegate::CreateStatic(&UPyCharmRemoteDebugNotifications::OpenSettings);
		Info.HyperlinkText = LOCTEXT("OpenSettingsLink", "Open PyCharm Remote Debug settings");
	}

	const TSharedPtr<SNotificationItem> Item = FSlateNotificationManager::Get().AddNotification(Info);
	if (Item.IsValid())
	{
		Item->SetCompletionState(bIsError ? SNotificationItem::CS_Fail : SNotificationItem::CS_Success);
	}
}

void UPyCharmRemoteDebugNotifications::OpenSettings()
{
	ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>(TEXT("Settings"));
	if (!SettingsModule)
	{
		UE_LOG(LogPyCharmRemoteDebug, Warning,
			TEXT("Settings module unavailable, open Project Settings > Plugins > PyCharm Remote Debug manually"));
		return;
	}

	// asked of the CDO so a rename cannot desync from the panel
	const UPyCharmRemoteDebugSettings* Settings = GetDefault<UPyCharmRemoteDebugSettings>();
	SettingsModule->ShowViewer(Settings->GetContainerName(), Settings->GetCategoryName(), Settings->GetSectionName());
}

#undef LOCTEXT_NAMESPACE
