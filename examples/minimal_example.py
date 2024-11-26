import json
from typing import List, Set, Tuple, Union, Literal
from enum import Enum
import basyx.aas.adapter.json

from aas_pydantic import AAS, Submodel, SubmodelElementCollection
import aas_pydantic


# Define custom enum
class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# Define a SubmodelElementCollection
class DeviceProperties(SubmodelElementCollection):
    serial_number: str
    firmware_version: str
    status: StatusEnum
    temperature_sensors: List[str]
    config_params: Set[str]


# Define a Submodel
class DeviceConfig(Submodel):
    id_short: str
    description: str
    properties: DeviceProperties
    measurements: List[float]
    settings: Union[str, int]


# Create an AAS
class DeviceAAS(AAS):
    device_info: DeviceConfig


# Create an example device
example_device = DeviceAAS(
    id="device_1",
    description="Example device",
    device_info=DeviceConfig(
        id_short="device_1_config",
        description="Device 1 Configuration",
        properties=DeviceProperties(
            id_short="device_1_properties",
            serial_number="1234",
            firmware_version="1.0",
            status=StatusEnum.ACTIVE,
            temperature_sensors=["sensor_1", "sensor_2"],
            config_params={"param_1", "param_2"},
        ),
        measurements=[1.0, 2.0, 3.0],
        settings="default",
    ),
)

# Create AAS template and serialize it to a file
aas_template_objectstore = aas_pydantic.convert_model_to_aas_template(DeviceAAS)

with open("aas_template_DeviceAAS.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(f, aas_template_objectstore)


# Create Submodel template and serialize it to a file
submodel_template = aas_pydantic.convert_model_to_submodel_template(DeviceConfig)
with open("submodel_template_DeviceConfig.json", "w") as f:
    json_string = json.dumps(
        submodel_template,
        cls=basyx.aas.adapter.json.AASToJsonEncoder,
    )
    f.write(json_string)

# Convert Pydantic model to BaSyx instances and serialize them to a file
basyx_submodel = aas_pydantic.convert_model_to_submodel(example_device.device_info)
basyx_objectstore = aas_pydantic.convert_model_to_aas(example_device)

with open("aas_instance_DeviceAAS.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(f, basyx_objectstore)


# create dynamically pydantic types from AAS and submodel templates
pydantic_aas_types = aas_pydantic.convert_object_store_to_pydantic_types(
    aas_template_objectstore
)
pydantic_submodel_type = aas_pydantic.convert_submodel_template_to_pydatic_type(
    submodel_template
)
print(pydantic_submodel_type.model_fields)


# Convert BaSyx back to Pydantic model
pydantic_submodel = aas_pydantic.convert_submodel_to_model_instance(
    basyx_submodel, model_type=pydantic_submodel_type
)
pydantic_aas = aas_pydantic.convert_object_store_to_pydantic_models(
    basyx_objectstore, pydantic_aas_types
)

print(pydantic_aas)
