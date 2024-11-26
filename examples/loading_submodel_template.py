import json
from pathlib import Path
import basyx.aas.adapter.json

import aas_pydantic


file_folder = Path(__file__).parent
# Loading the IDTA submodel template from a file
with open(
    file_folder / "IDTA 02045-1-0_Template_DataModelForAssetLocation.json", "r"
) as file:
    basyx_object_store = basyx.aas.adapter.json.read_aas_json_file(file)

# Convert the basyx object store to pydantic types
pydantic_types = aas_pydantic.convert_object_store_to_pydantic_types(basyx_object_store)

assert len(pydantic_types) == 1 #  only one model contained for the submodel template

# serialize the pydantic types as JSON Schema to a file
with open("pydantic_types.json", "w") as f:
    json.dump(pydantic_types[0].model_json_schema(), f, indent=2)

# with data model code generator, you can generate the pydantic model from the json schema and work easily with IDTA submodel templates.