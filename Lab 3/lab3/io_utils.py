import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_csv(data: List[Dict[str, Any]], output_path: Path, fieldnames: Iterable[str]) -> None:
    ensure_parent_dir(output_path)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        if data:
            writer.writerows(data)

    print(f"Saved: {output_path}")
    print(f"Rows: {len(data)}")


def load_csv(input_path: Path) -> List[Dict[str, str]]:
    if not input_path.exists():
        raise FileNotFoundError(f"CSV not found: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)
