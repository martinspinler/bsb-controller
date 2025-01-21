import argparse
from .server import run
from .messages import messages_by_name

from schema import Schema, Or, Optional
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='BSB controller')
    parser.add_argument("-c", "--config", help="Configuration file")

    args = parser.parse_args()

    return args


config_schema = Schema(
    {
        'bsbport': str,
        Optional('mqtt'): {
            'connection': {
                'addr': str,
                'port': int,
            },
            Optional('allow_set'): [
                *messages_by_name.keys(),
            ],
            Optional('rename'): {
                Or(*messages_by_name.keys()): str,
            }
        },
        'requests': [
            Or(
                *messages_by_name.keys(),
                {Or(*messages_by_name.keys(), only_one=True): int},
            )
        ],
    }
)

args = parse_args()

with open(args.config) as f:
    config = yaml.safe_load(f)
config_schema.validate(config)

requests = {(list(k.keys())[0] if isinstance(k, dict) else k): (list(k.values())[0] if isinstance(k, dict) else None) for k in config['requests']}
monitored_messages = {messages_by_name[k]: v for k, v in requests.items()}

run(config, monitored_messages)
