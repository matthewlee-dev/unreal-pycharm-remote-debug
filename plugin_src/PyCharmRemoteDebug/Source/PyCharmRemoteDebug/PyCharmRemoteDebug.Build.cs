using UnrealBuildTool;

public class PyCharmRemoteDebug : ModuleRules
{
	public PyCharmRemoteDebug(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"CoreUObject",
			"Engine",
			"Slate",
			"SlateCore",
			"ToolMenus",
			"DeveloperSettings",
			"PythonScriptPlugin",
		});
	}
}
