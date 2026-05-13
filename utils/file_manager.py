from pathlib import Path

import pandas as pd

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
RESULT_DIR = Path(__file__).resolve().parent.parent / "results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def save_uploaded(uploaded_file) -> Path:
    dest = UPLOAD_DIR / uploaded_file.name
    dest.write_bytes(uploaded_file.getbuffer())
    return dest


def list_files() -> list[str]:
    return sorted(
        f.name for f in UPLOAD_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    )


def delete_file(name: str) -> bool:
    path = UPLOAD_DIR / name
    if path.exists() and path.parent == UPLOAD_DIR:
        path.unlink()
        return True
    return False


def preview_file(name: str, nrows: int = 5) -> pd.DataFrame | None:
    path = UPLOAD_DIR / name
    if not path.exists():
        return None
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, nrows=nrows)
    return pd.read_excel(path, nrows=nrows)


def read_file(name: str) -> pd.DataFrame | None:
    path = UPLOAD_DIR / name
    if not path.exists():
        return None
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def build_file_context(mode: str = "chat") -> str:
    files = list_files()
    if not files:
        return ""

    if mode == "codegen":
        parts = ["## Available files:\n"]
        for fname in files:
            df = read_file(fname)
            if df is None:
                continue
            parts.append(
                f'files["{fname}"]  # {len(df)} rows x {len(df.columns)} columns'
            )
            parts.append(f"  Columns: {', '.join(df.columns.astype(str))}")
            parts.append(f"  Dtypes: {dict(df.dtypes.astype(str))}")
            parts.append("  Sample (first 5 rows):")
            parts.append(df.head(5).to_string(index=False))
            parts.append("")
        return "\n".join(parts)

    parts = ["The user has uploaded the following files:\n"]
    for fname in files:
        df = read_file(fname)
        if df is None:
            continue
        parts.append(f"## File: {fname} ({len(df)} rows × {len(df.columns)} columns)")
        parts.append(f"Columns: {', '.join(df.columns.astype(str))}")
        parts.append(df.head(20).to_string(index=False))
        if len(df) > 20:
            parts.append(f"... ({len(df) - 20} more rows)")
        parts.append("")
    return "\n".join(parts)


def list_results() -> list[str]:
    return sorted(
        f.name for f in RESULT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    )


def delete_result(name: str) -> bool:
    path = RESULT_DIR / name
    if path.exists() and path.parent == RESULT_DIR:
        path.unlink()
        return True
    return False


def get_file_info(name: str) -> dict | None:
    path = UPLOAD_DIR / name
    if not path.exists():
        return None
    size = path.stat().st_size
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "size_kb": round(size / 1024, 1),
    }
