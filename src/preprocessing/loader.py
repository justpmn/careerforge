from pathlib import Path
from zipfile import ZipFile
import pandas as pd

def load_parquet(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_parquet(file_path)

def load_text(file_path: Path, encoding: str = "utf-8") -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.read_text(encoding=encoding)

def list_zip_files(zip_path: Path) -> list[str]:
    if not zip_path.exists():
        raise FileNotFoundError(f"File not found: {zip_path}")

    with ZipFile(zip_path, "r") as archive:
        return archive.namelist()

def load_csv_from_zip(
    zip_path: Path,
    member_name: str,
    **read_csv_kwargs
) -> pd.DataFrame:
    if not zip_path.exists():
        raise FileNotFoundError(f"File not found: {zip_path}")

    with ZipFile(zip_path, "r") as archive:
        if member_name not in archive.namelist():
            raise FileNotFoundError(
                f"{member_name} not found inside {zip_path.name}"
            )

        with archive.open(member_name) as csv_file:
            return pd.read_csv(csv_file, **read_csv_kwargs)
        
def load_csv(file_path: Path, **read_csv_kwargs) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path, **read_csv_kwargs)