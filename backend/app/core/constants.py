import json
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.parent

try:
    sys.path.insert(0, str(root_dir))
    from shared.constants_schema import Constants  # noqa: E402
finally:
    sys.path.remove(str(root_dir))

shared_dir = root_dir / 'shared'
constants_json_path = shared_dir / 'constants.json'

with open(constants_json_path, 'r') as f:
    constants_data = json.load(f)

# shared constants object
constants = Constants.model_validate(constants_data)

job_description_constants = constants.job_description_constants
response_constants = constants.response_constants
