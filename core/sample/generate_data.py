import json
from pathlib import Path

def generate_scenario3_instance(
    output_path: str = "../data/instance/scenario3.json",
):
    instance = {
        "name": "Scenario3",
        "nodes": [
            "s",
            "a",
            "b",
            "t",
            "c",
            "d",
        ],

        "links": [
            {"id": 1, "u": "s", "v": "a", "length": 1, "slots": 5},
            {"id": 2, "u": "a", "v": "b", "length": 1, "slots": 5},
            {"id": 3, "u": "b", "v": "t", "length": 1, "slots": 5},

            {"id": 4, "u": "s", "v": "c", "length": 1, "slots": 5},
            {"id": 5, "u": "c", "v": "t", "length": 1, "slots": 5},

            {"id": 6, "u": "s", "v": "d", "length": 1, "slots": 5},
            {"id": 7, "u": "d", "v": "t", "length": 1, "slots": 5},
        ],

        "demands": [
            {"id": 1, "source": "s", "target": "t", "slots": 4},
            {"id": 2, "source": "s", "target": "t", "slots": 3},
            {"id": 3, "source": "s", "target": "t", "slots": 2},
        ],

        "nominal_paths": {
            "1": {
                "path": ["s", "a", "b", "t"],
                "last_slot": 4,
                "slot_block": [1, 2, 3, 4],
            },
            "2": {
                "path": ["s", "c", "t"],
                "last_slot": 4,
                "slot_block": [2, 3, 4],
            },
            "3": {
                "path": ["s", "d", "t"],
                "last_slot": 4,
                "slot_block": [3, 4],
            },
        },

        "failure": {
            "failed_links": [["a", "b"]]
        },
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(instance, f, indent=2)

    print(f"[OK] Scenario 3 instance saved to: {output_file}")


if __name__ == "__main__":
    generate_scenario3_instance()
