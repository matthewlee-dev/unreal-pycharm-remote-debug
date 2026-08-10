import unreal

"""
1: For user acceptance testing, add a breakpoint in the below module
2. Start PyCharm debugger
3. Start Unreal debugger
4. run the following in unreal and make sure break point gets hit:

    import sys
    sys.path.append("/Users/sunnyday-mini/Developer/unreal_pycharm_debug/tests/uat/")
    import material_build
    material_build.main()
5. detach, reconnect, make sure we can still hit the breakpoint
"""


def create_material_asset(asset_name, package_path):
    """Creates a new blank material asset in the content browser.

    Args:
        asset_name: Name of the material asset to create.
        package_path: Content browser path to create the asset in.

    Returns:
        The created Material object, or None if creation failed.
    """
    full_path = f"{package_path}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        unreal.EditorAssetLibrary.delete_asset(full_path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    material = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.Material,
        factory=factory,
    )
    if not material:
        unreal.log_error(f"Failed to create material: {asset_name}")
    return material


def add_expression(material, expression_class, x, y):
    """Adds a material expression node to a material at the given graph position.

    Args:
        material: The Material object to add the expression to.
        expression_class: The unreal expression class to instantiate.
        x: Horizontal position in the material graph.
        y: Vertical position in the material graph.

    Returns:
        The created material expression node.
    """
    return unreal.MaterialEditingLibrary.create_material_expression(
        material, expression_class, x, y
    )


def add_texture_sample(material, texture_path, x, y):
    """Adds a TextureSample node loaded from the given asset path.

    Args:
        material: The Material object to add the node to.
        texture_path: Content browser path to the texture asset.
        x: Horizontal position in the material graph.
        y: Vertical position in the material graph.

    Returns:
        The created MaterialExpressionTextureSample node.
    """
    node = add_expression(material, unreal.MaterialExpressionTextureSample, x, y)
    texture = unreal.load_asset(texture_path)
    node.set_editor_property("texture", texture)
    return node


def add_vector_parameter(material, parameter_name, default_value, x, y):
    """Adds a VectorParameter node with a given name and default color value.

    Args:
        material: The Material object to add the node to.
        parameter_name: Exposed parameter name shown in material instances.
        default_value: A unreal.LinearColor to use as the default.
        x: Horizontal position in the material graph.
        y: Vertical position in the material graph.

    Returns:
        The created MaterialExpressionVectorParameter node.
    """
    node = add_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", parameter_name)
    node.set_editor_property("default_value", default_value)
    return node


def add_scalar_parameter(material, parameter_name, default_value, x, y):
    """Adds a ScalarParameter node with a given name and default float value.

    Args:
        material: The Material object to add the node to.
        parameter_name: Exposed parameter name shown in material instances.
        default_value: Float value to use as the default.
        x: Horizontal position in the material graph.
        y: Vertical position in the material graph.

    Returns:
        The created MaterialExpressionScalarParameter node.
    """
    node = add_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", parameter_name)
    node.set_editor_property("default_value", default_value)
    return node


def connect_expressions(from_node, from_pin, to_node, to_pin):
    """Connects two material expression nodes by their pin names.

    Args:
        from_node: The source expression node.
        from_pin: Output pin name on the source node. Use "" for default.
        to_node: The destination expression node.
        to_pin: Input pin name on the destination node. Use "" for default.
    """
    unreal.MaterialEditingLibrary.connect_material_expressions(
        from_node, from_pin, to_node, to_pin
    )


def connect_to_output(node, output_pin, material_property):
    """Connects a material expression node to a root material output property.

    Args:
        node: The expression node to connect from.
        output_pin: Output pin name on the node. Use "" for default.
        material_property: A unreal.MaterialProperty enum value (e.g. MP_BASE_COLOR).
    """
    unreal.MaterialEditingLibrary.connect_material_property(
        node, output_pin, material_property
    )


def compile_and_save(material):
    """Recompiles a material and saves it to disk.

    Args:
        material: The Material object to recompile and save.
    """
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material.get_path_name())
    unreal.log(f"Material saved: {material.get_path_name()}")


def main():
    """Creates a simple material with a tinted texture sample and roughness control.

    Used for testing the PyCharmRemoteDebug plugin integration.

    Builds the following graph:
        TextureSample (RGB) ---> Multiply --> BaseColor
        TintColor (Vector) ---> Multiply
        Roughness (Scalar) ---> Roughness
    """
    material = create_material_asset(
        "M_PyCharmRemoteDebugTestingProceduralMaterial",
        "/Game/PyCharmRemoteDebugTesting",
    )
    if not material:
        return

    texture_node = add_texture_sample(
        material, "/Engine/EngineMaterials/DefaultDiffuse", -400, 0
    )
    tint_node = add_vector_parameter(
        material, "TintColor", unreal.LinearColor(1, 1, 1, 1), -400, -200
    )
    multiply_node = add_expression(
        material, unreal.MaterialExpressionMultiply, -150, -100
    )
    roughness_node = add_scalar_parameter(material, "Roughness", 0.5, -400, 200)

    connect_expressions(texture_node, "RGB", multiply_node, "A")
    connect_expressions(tint_node, "", multiply_node, "B")
    connect_to_output(multiply_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    connect_to_output(roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS)

    compile_and_save(material)
