# AAS Pydantic
![Build-sucess](https://img.shields.io/badge/build-success-green)
![PyPI](https://img.shields.io/pypi/v/aas_pydantic)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aas_pydantic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A Python package that combines the BaSyx Python SDK for handling Asset Administration Shells (AAS) with Pydantic models for fast and easy modeling and transformation of Industry 4.0 data structures.

The package enables:

- Creating AAS models using Pydantic's intuitive syntax
- Converting between Pydantic models and BaSyx AAS instances
- Converting IDTA submodel templates to Pydantic types and vice versa
- Serialization to JSON/Schema formats for easy integrations with other tools


## Installation

You can install the package using pip:

```bash
pip install aas-pydantic
```

Note that the package requires python 3.10 or higher.

## Usage

The package provides a set of Pydantic models that can be used to create AAS models. The models are based on the BaSyx SDK and are designed to be easily converted to and from AAS instances.

In the following example, we create a simple AAS of a Device with one Submodel DeviceConfig. 

```python
from typing import List, Set, Union
from enum import Enum
from aas_pydantic import AAS, Submodel, SubmodelElementCollection

# Define custom enums
class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Define SubmodelElementCollections
class DeviceProperties(SubmodelElementCollection):
    serial_number: str
    firmware_version: str
    status: StatusEnum
    temperature_sensors: List[str]
    config_params: Set[str]

# Define Submodels
class DeviceConfig(Submodel):
    id_short: str
    description: str
    properties: DeviceProperties
    measurements: List[float]
    settings: Union[str, int]

# Create AAS class
class DeviceAAS(AAS):
    device_info: DeviceConfig
```

We also want to create an instance of this model, which we will use later:

```python
device = DeviceAAS(
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
            config_params={"param_1", "param_2"}
        ),
        measurements=[1.0, 2.0, 3.0],
        settings="default"
    )
)
```

## Model Conversion

The package provides methods for converting between Pydantic models and BaSyx models. This works both for pydantic types / basyx templates and instances.

### Convert Pydantic model to BaSyx templates

At first, we want to show an submodel template can be created from the modelled type:

```python
submodel_template = aas_pydantic.convert_model_to_submodel_template(DeviceConfig)
```

For inspection of the submodel template, we can serialize it to a file:

```python
import basyx.aas.adapter.json

with open("submodel_template_DeviceConfig.json", "w") as f:
    json_string = json.dumps(
        submodel_template,
        cls=basyx.aas.adapter.json.AASToJsonEncoder,
    )
    f.write(json_string)
```

We can also convert a whole AAS type to a Basyx Object Store:

```python
aas_template_objectstore = aas_pydantic.convert_model_to_aas_template(DeviceAAS)
```

We can also serialize the AAS template to a file:

```python
with open("aas_template_DeviceAAS.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(
        f, aas_template_objectstore
    )
```

### Convert Pydantic model instance to BaSyx instance

We can also convert an instance of the Pydantic model to a BaSyx instance:

```python
basyx_objectstore = aas_pydantic.convert_model_to_aas(example_device)
```

When we convert a pydantic AAS model to a basyx instance, we obtain an object store, holding the AAS and its submodels. We can serialize this object store to a file:

```python
with open("aas_instance_DeviceAAS.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(f, basyx_objectstore)
```

Only converting a single submodel instance is also possible:

```python
basyx_submodel = aas_pydantic.convert_model_to_submodel(example_device.device_info)
```

### Convert BaSyx templates to pydantic types

In aas-pydantic you can create pydantic types from BaSyx templates at runtime. This can be useful when you want to create a Pydantic model from an existing AAS data structure. 


```python	
pydantic_aas_types = aas_pydantic.convert_object_store_to_pydantic_types(
    aas_template_objectstore
)
pydantic_submodel_type = aas_pydantic.convert_submodel_template_to_pydatic_type(
    submodel_template
)
print(pydantic_submodel_type.model_fields)
```

This conversion significantly reduces data complexity since relying of flat object structures instead of the AAS Meta Model. Moreover, since pydantic has many integration, such as JSonSchema or fastAPI, this transformation can be useful for many use cases.


## Convert BaSyx instances to Pydantic instances

In aas-pydantic you can also convert BaSyx instances to Pydantic instances. This can be useful when you want to work with Pydantic models in your application, but need to convert them to BaSyx instances for communication with other systems.

For conversion of the instances, you require the previously generated Pydantic types:

```python
pydantic_submodel = aas_pydantic.convert_submodel_to_model_instance(basyx_submodel, model_type=pydantic_submodel_type)
pydantic_aas = aas_pydantic.convert_object_store_to_pydantic_models(
    basyx_objectstore, pydantic_aas_types
)
print(pydantic_aas)
```

## Working with IDTA Submodel Templates

Previously, we have shown how submodel templates can be loaded. Of course, this is also possible for submodel templates obtained from IDTA. For example, we can load to submodel template for [Data Model for Asset Location (Version 1.0](https://github.com/admin-shell-io/submodel-templates/tree/main/published/Data%20Model%20for%20Asset%20Location/1/0):

```python
import aas_pydantic
import basyx.aas.adapter.json

with open(
    "IDTA 02045-1-0_Template_DataModelForAssetLocation.json", "r"
) as file:
    basyx_object_store = basyx.aas.adapter.json.read_aas_json_file(file)
pydantic_types = aas_pydantic.convert_object_store_to_pydantic_types(basyx_object_store)
with open("pydantic_types.json", "w") as f:
    json.dump(pydantic_types[0].model_json_schema(), f, indent=2)

```

This example shows, how simple integration between Submodel templates and JSON Schema can be achieved. The geneated JSON Schema could, e.g. be used in code [generation tools for pydantic models](https://github.com/koxudaxi/datamodel-code-generator) to have defined pydantic types for the submodel templates.


## Conversion Capabilities

The package provides the following conversion of python type annotations:

- Primitive types (int, float, str, bool)
- Collections (List, Set, Tuples)
- Enums and Literals
- Unions and Optional types
- Nested Pydantic models

Note that dicts are not supported, since a clear distinction from SubmodelElementCollection to the dict or pydantic type is not possible.

The following BaSyx Submodel Element Types are supported:
- SubmodelElementCollection
- SubmodelElementList
- ReferenceElement
- RelationshipElement
- Property
- Blob
- File

During conversion, the following information will be preserved:
- Identifiers
- Descriptions
- Semantic Identifiers
- Values and Value Types

Storage of additional information that cannot be kept easily in the BaSyx model (attribute and class names, optional and union types, enums) will be stored in the Concept Descriptions of the BaSyx model.

## License

The package is licensed under the [MIT license](LICENSE).