# © 2022 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between Customer and either
# Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.

from typing import Dict
from benedict import benedict


# Load configuration
def load_config() -> Dict:
    # Load common file
    try:
        common_config = benedict.from_yaml("config/config.yaml")
    except ValueError:
        print("No config found in config/config.yaml")
        common_config = benedict([])

    return common_config
