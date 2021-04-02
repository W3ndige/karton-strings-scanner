import re
import requests
import hashlib

from typing import Dict, Any
from karton.core import Karton, Task, Config


SUS_KEYWORDS = [
    r".*pdb$",
    r"(Mozilla)\/[0-9]\.[0.9].*",
    r"http://.*",
]

HEURISTICS = {
    "PDB": [r".*pdb$"],
    "User-Agent": [r"(Mozilla)\/[0-9]\.[0.9].*"],
    "URL": [r"https?://.*"],
    "REG": [r"HKEY_.{1,20}\\"],
}


class AuroraConfig(Config):
    def __init__(self, path=None) -> None:
        super().__init__(path)
        self.aurora_config = dict(self.config.items("aurora"))


def post_string_to_sample(url: str, sha256: str, string_input=Dict[str, Any]) -> Dict:
    r = requests.post(f"{url}/sample/{sha256}/string", json=string_input)

    return r.json()


class StringsScanner(Karton):
    identity = "karton.strings_scanner"
    filters = [
        {
            "type": "feature",
            "stage": "raw",
            "kind": "strings"
        }
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.compiled_heuristics = {}
        for heuristic_name in HEURISTICS.keys():
            tmp_compiled_heuristics = []
            for heuristic in HEURISTICS[heuristic_name]:
                tmp_compiled_heuristics.append(re.compile(heuristic))

            self.compiled_heuristics[heuristic_name] = tmp_compiled_heuristics

    def process(self, task: Task) -> None:
        strings = task.get_payload("data")
        sha256 = task.get_payload("sha256")

        for string in strings:
            for heuristic_name in self.compiled_heuristics.keys():
                for heuristic in self.compiled_heuristics[heuristic_name]:
                    if re.match(heuristic, string):
                        string_hash = hashlib.sha256(
                            bytes(string, encoding="UTF-8")
                        ).hexdigest()

                        post_string_to_sample(
                            self.config.aurora_config["url"],
                            sha256,
                            {
                                "value": string,
                                "sha256": string_hash,
                                "heuristic": heuristic_name,
                            }
                        )
