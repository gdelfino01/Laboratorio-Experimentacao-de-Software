import csv
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


def save_csv(data: List[Dict[str, Any]], filename: Path) -> None:
    if not data:
        raise ValueError("Nenhum dado para salvar.")

    filename.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(data[0].keys())

    with filename.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f" Dados salvos em '{filename}'")
    print(f"   Total de linhas: {len(data)}")


def run_subprocess(command: List[str], cwd: Optional[Path] = None) -> None:
    printable_command = " ".join(command)
    print(f"$ {printable_command}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def sanitize_repo_name(name_with_owner: str) -> str:
    return name_with_owner.replace("/", "__")
