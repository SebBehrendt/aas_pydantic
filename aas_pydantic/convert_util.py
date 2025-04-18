import datetime
import json
from types import NoneType
from typing import Any, Dict, List, Union
import uuid
from basyx.aas import model

import typing
import stringcase

from basyx.aas.model import datatypes
from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo

from aas_pydantic import aas_model


class AttributeFieldInfo(BaseModel):
    name: str
    field_info: FieldInfo

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AttributeInfo(AttributeFieldInfo):
    value: Any


def get_attribute_field_infos(
    obj: Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ]
) -> List[AttributeFieldInfo]:
    """
    Returns a dictionary of all attributes of an object that are not None, do not start with an underscore and are not standard attributes of the aas object.

    Args:
        obj (Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]): Object to get the attributes from
    Returns:
        List[AttributeFieldInfo]: List of attributes of the object
    """
    attribute_infos = []
    for attribute_name, field_info in obj.model_fields.items():
        if attribute_name in ["id", "description", "id_short", "semantic_id"]:
            continue
        if attribute_name.startswith("_"):
            continue
        attribute_infos.append(
            AttributeFieldInfo(name=attribute_name, field_info=field_info)
        )
    return attribute_infos


def get_attribute_infos(
    obj: Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]
) -> List[AttributeInfo]:
    """
    Returns a dictionary of all attributes of an object that are not None, do not start with an underscore and are not standard attributes of the aas object.

    Args:
        obj (Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]): Object to get the attributes from

    Returns:
        List[AttributeInfo]: List of attributes of the object
    """
    attribute_infos = []
    for attribute_name, field_info in obj.model_fields.items():
        if attribute_name in ["id", "description", "id_short", "semantic_id"]:
            continue
        if attribute_name.startswith("_"):
            continue
        attribute_value = getattr(obj, attribute_name)
        attribute_infos.append(
            AttributeInfo(
                name=attribute_name, field_info=field_info, value=attribute_value
            )
        )
    return attribute_infos


def get_str_description(langstring_set: model.LangStringSet) -> str:
    """
    Converts a LangStringSet to a string.
    Args:
        langstring_set (model.LangStringSet): LangStringSet to convert
    Returns:
        str: String representation of the LangStringSet
    """
    if not langstring_set:
        return ""
    if "en" in langstring_set:
        return str(langstring_set.get("en"))
    elif "ger" in langstring_set:
        return str(langstring_set.get("ger"))
    elif "de" in langstring_set:
        return str(langstring_set.get("de"))
    else:
        return str(langstring_set.get(list(langstring_set.keys())[0]))


def get_basyx_description_from_model(
    model_object: (
        aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection
    ),
) -> model.LangStringSet:
    """
    Creates a LangStringSet from an aas model.
    Args:
        model_object (aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection): The model to get the description from.
    Returns:
        model.LangStringSet: LangStringSet description representation of the model object
    Raises:
        ValueError: If the description of the model object is not a dict or a string
    """
    if not model_object.description:
        return None
    try:
        dict_description = json.loads(model_object.description)
        if not isinstance(dict_description, dict):
            raise ValueError
    except ValueError:
        dict_description = {"en": model_object.description}
    return model.LangStringSet(dict_description)


def get_class_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ]
) -> str:
    """
    Returns the class name of an basyx model from the data specifications.

    Args:
        item (model.HasDataSpecification): Basyx model to get the class name from

    Raises:
        ValueError: If no data specifications are found in the item or if no class name is found

    Returns:
        str: Class name of the basyx model
    """
    if not item.embedded_data_specifications:
        return item.id_short
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not content.preferred_name.get("en") == "class":
            continue
        condition_smc = any(
            key.value == item.id_short for key in data_spec.data_specification.key
        )
        condition_aas_sm = hasattr(item, "id") and any(
            key.value == item.id for key in data_spec.data_specification.key
        )
        if not condition_smc and not condition_aas_sm:
            continue

        return content.value
    raise ValueError(
        f"No class name found in item with id {item.id_short} and type {type(item)}"
    )


def get_class_name_from_basyx_template(
    item: typing.Union[model.Submodel, model.SubmodelElementCollection]
) -> str:
    """
    Returns the class name of an basyx model from the data specifications.

    Args:
        item (model.HasDataSpecification): Basyx model to get the class name from

    Raises:
        ValueError: If no data specifications are found in the item or if no class name is found

    Returns:
        str: Class name of the basyx model
    """
    if not item.embedded_data_specifications:
        return stringcase.camelcase(item.id_short)
    return get_class_name_from_basyx_model(item)


def get_attribute_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id: str,
) -> List[str]:
    """
    Returns the attribute name of the referenced element of the item.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        str: The attribute name of the referenced item
    """
    if not item.embedded_data_specifications:
        return stringcase.snakecase(referenced_item_id)
    attribute_names = []
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not any(
            key.value == referenced_item_id for key in data_spec.data_specification.key
        ):
            continue
        if not content.preferred_name.get("en") == "attribute":
            continue
        attribute_names.append(content.value)
    if attribute_names:
        return attribute_names
    raise ValueError(
        f"Attribute reference to {referenced_item_id} could not be found in {item.id_short} of type {type(item)}"
    )


def get_attribute_names_from_basyx_template(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id_short: str,
) -> List[str]:
    """
    Returns the attribute name of the referenced element of the item.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        str: The attribute name of the referenced item
    """
    if not item.embedded_data_specifications:
        return [stringcase.snakecase(referenced_item_id_short)]
    return get_attribute_name_from_basyx_model(item, referenced_item_id_short)


def get_data_specification_for_model_template(
    model_type: typing.Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ],
) -> typing.List[model.EmbeddedDataSpecification]:
    return [
        model.EmbeddedDataSpecification(
            data_specification=model.ExternalReference(
                key=(
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value=(get_template_id(model_type)),
                    ),
                ),
            ),
            data_specification_content=model.DataSpecificationIEC61360(
                preferred_name=model.LangStringSet({"en": "class"}),
                value=get_template_id(model_type),
            ),
        )
    ]


def get_data_specification_for_model(
    item: typing.Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ],
) -> typing.List[model.EmbeddedDataSpecification]:
    return [
        model.EmbeddedDataSpecification(
            data_specification=model.ExternalReference(
                key=(
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value=(
                            item.id
                            if isinstance(
                                item, typing.Union[aas_model.AAS, aas_model.Submodel]
                            )
                            else item.id_short
                        ),
                    ),
                ),
            ),
            data_specification_content=model.DataSpecificationIEC61360(
                preferred_name=model.LangStringSet({"en": "class"}),
                value=item.__class__.__name__.split(".")[-1],
            ),
        )
    ]


def get_model_keys_for_data_specification(
    item: typing.Union[
        NoneType, aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ] = None,
) -> typing.Tuple[model.Key]:
    if item is None:
        return (
            model.Key(
                type_=model.KeyTypes.GLOBAL_REFERENCE,
                value=uuid.uuid4().hex,
            ),
        )
    return (
        model.Key(
            type_=model.KeyTypes.GLOBAL_REFERENCE,
            value=(
                item.id
                if isinstance(item, typing.Union[aas_model.AAS, aas_model.Submodel])
                else item.id_short
            ),
        ),
    )


def get_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo, basyx_attribute: Any
) -> model.EmbeddedDataSpecification:
    model_keys = get_model_keys_for_data_specification(basyx_attribute)
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "attribute"}),
            value=attribute_field_info.name,
        ),
    )


def get_optional_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not (
        typing.get_origin(attribute_field_info.field_info.annotation) is Union
        and type(None) in typing.get_args(attribute_field_info.field_info.annotation)
    ):
        return
    model_keys = get_model_keys_for_data_specification()

    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "optional"}),
            value=attribute_field_info.name,
        ),
    )


def get_immutable_data_specification_for_attribute_name(
    attribute_name: str,
) -> model.EmbeddedDataSpecification:
    model_keys = get_model_keys_for_data_specification()
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "immutable"}),
            value=attribute_name,
        ),
    )


def get_immutable_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not typing.get_origin(attribute_field_info.field_info.annotation) == tuple:
        return
    return get_immutable_data_specification_for_attribute_name(
        attribute_field_info.name
    )


def get_default_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
    basyx_attribute: typing.Union[
        NoneType, aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ],
) -> typing.Optional[model.EmbeddedDataSpecification]:
    model_keys = get_model_keys_for_data_specification(basyx_attribute)
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "default"}),
            value=attribute_field_info.field_info.default,
        ),
    )


def get_union_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not (
        typing.get_origin(attribute_field_info.field_info.annotation) == Union
        and len(
            [
                arg
                for arg in typing.get_args(attribute_field_info.field_info.annotation)
                if arg != NoneType
            ]
        )
        > 1
    ):
        return
    model_keys = get_model_keys_for_data_specification()

    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "union"}),
            value=attribute_field_info.name,
        ),
    )


def get_default_value_from_basyx_model(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_id: str,
) -> typing.Any:
    """
    Returns the default value of an attribute

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The item to check
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (content.preferred_name.get("en") == "default"):
            continue
        if not any(
            key.value == attribute_id for key in data_spec.data_specification.key
        ):
            continue
        return content.value
    return


def is_attribute_from_basyx_model_immutable(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if the referenced item of the item is immutable.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        bool: If the referenced item is immutable
    """
    if not item.embedded_data_specifications:
        return False
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not content.preferred_name.get("en") == "immutable":
            continue
        return content.value == attribute_name
    return False


def is_optional_attribute_type(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if an attribute of an aas is optional.

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The item to check
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return True
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (
            content.preferred_name.get("en") == "optional"
            and content.value == attribute_name
        ):
            continue
        return True
    return False


def is_union_attribute_type(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if an attribute of an aas is optional.

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): Aas to get the attribute from
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return False
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (
            content.preferred_name.get("en") == "union"
            and content.value == attribute_name
        ):
            continue
        return True
    return False


def get_template_id(
    element: Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ]
) -> str:
    return element.__name__.split(".")[-1]


def get_id_short(
    element: Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ]
) -> str:
    if element.id_short:
        return element.id_short
    else:
        return element.id


def get_semantic_id(
    model_object: aas_model.Submodel | aas_model.SubmodelElementCollection,
) -> str | None:
    if model_object.semantic_id:
        semantic_id = model.ExternalReference(
            key=(model.Key(model.KeyTypes.GLOBAL_REFERENCE, model_object.semantic_id),)
        )
    else:
        semantic_id = None
    return semantic_id


def get_value_type_of_attribute(
    attribute: Union[str, int, float, bool]
) -> model.datatypes:
    if isinstance(attribute, bool):
        return model.datatypes.Boolean
    elif isinstance(attribute, int):
        return model.datatypes.Integer
    elif isinstance(attribute, float):
        return model.datatypes.Double
    else:
        return model.datatypes.String


def get_semantic_id_value_of_model(
    basyx_model: typing.Union[model.Submodel, model.SubmodelElement]
) -> str:
    """
    Returns the semantic id of a submodel or submodel element.

    Args:
        basyx_model (model.Submodel | model.SubmodelElement): Basyx model to get the semantic id from.

    Returns:
        str: Semantic id of the model.
    """
    if not isinstance(basyx_model, model.HasSemantics):
        raise NotImplementedError("Type not implemented:", type(basyx_model))
    if not basyx_model.semantic_id:
        return ""
    return basyx_model.semantic_id.key[0].value


def convert_xsdtype_to_primitive_type(
    xsd_data_type: model.DataTypeDefXsd,
) -> aas_model.PrimitiveSubmodelElement:
    if xsd_data_type == datatypes.Duration:
        return str
    elif xsd_data_type == datatypes.DateTime:
        return datetime.datetime
    elif xsd_data_type == datatypes.Date:
        return datetime.datetime
    elif xsd_data_type == datatypes.Time:
        return datetime.time
    # TODO: implement GyearMonth, GYer, GMonthDay, GDay, GMonth
    elif xsd_data_type == datatypes.Boolean:
        return bool
    elif xsd_data_type == datatypes.Base64Binary:
        return bytes
    elif xsd_data_type == datatypes.HexBinary:
        return bytes
    elif xsd_data_type == datatypes.Float:
        return float
    elif xsd_data_type == datatypes.Double:
        return float
    elif xsd_data_type == datatypes.Decimal:
        return float
    elif xsd_data_type == datatypes.Integer:
        return int
    elif xsd_data_type == datatypes.Long:
        return int
    elif xsd_data_type == datatypes.Int:
        return int
    elif xsd_data_type == datatypes.Short:
        return int
    elif xsd_data_type == datatypes.Byte:
        return int
    elif xsd_data_type == datatypes.NonPositiveInteger:
        return int
    elif xsd_data_type == datatypes.NegativeInteger:
        return int
    elif xsd_data_type == datatypes.NonNegativeInteger:
        return int
    elif xsd_data_type == datatypes.PositiveInteger:
        return int
    elif xsd_data_type == datatypes.UnsignedLong:
        return int
    elif xsd_data_type == datatypes.UnsignedInt:
        return int
    elif xsd_data_type == datatypes.UnsignedShort:
        return int
    elif xsd_data_type == datatypes.UnsignedByte:
        return int
    elif xsd_data_type == datatypes.AnyURI:
        return str
    elif xsd_data_type == datatypes.String:
        return str
    elif xsd_data_type == datatypes.NormalizedString:
        return str


def convert_primitive_type_to_xsdtype(
    primitive_type: aas_model.PrimitiveSubmodelElement,
) -> model.DataTypeDefXsd:
    if primitive_type == str:
        return datatypes.String
    elif primitive_type == datetime.datetime:
        return datatypes.DateTime
    elif primitive_type == datetime.time:
        return datatypes.Time
    elif primitive_type == bool:
        return datatypes.Boolean
    elif primitive_type == bytes:
        return datatypes.Base64Binary
    elif primitive_type == float:
        return datatypes.Double
    elif primitive_type == int:
        return datatypes.Integer
    else:
        raise NotImplementedError("Type not implemented:", primitive_type)


def unpatch_id_short_from_temp_attribute(smec: model.SubmodelElementCollection):
    """
    Unpatches the id_short attribute of a SubmodelElementCollection from the temporary attribute.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to unpatch.
    """
    if not smec.id_short.startswith("generated_submodel_list_hack_"):
        return smec
    no_temp_values = []
    id_short = None
    for sm_element in smec.value:
        if isinstance(sm_element, model.Property) and sm_element.id_short.startswith(
            "temp_id_short_attribute"
        ):
            id_short = sm_element.value
            continue
        no_temp_values.append(sm_element)

    if not id_short:
        # return smec
        new_id_short = smec.parent.id_short
        smec.parent = None
        smec.id_short = new_id_short
        return smec

    for value in no_temp_values:
        smec.value.remove(value)
    new_smec = model.SubmodelElementCollection(
        id_short=id_short,
        value=no_temp_values,
        embedded_data_specifications=smec.embedded_data_specifications,
    )
    return new_smec


def repatch_id_short_to_temp_attribute(
    smec: model.SubmodelElementCollection, temp_smec: model.SubmodelElementCollection
):
    """
    Repatches the id_short attribute of a SubmodelElementCollection to the temporary attribute.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to repatch.
    """
    values_to_repatch = []
    for sm_element in temp_smec.value:
        values_to_repatch.append(sm_element)
    temp_smec.value.clear()
    for sm_element in values_to_repatch:
        smec.value.add(sm_element)
    return smec
