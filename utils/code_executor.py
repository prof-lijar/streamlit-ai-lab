from __future__ import annotations

import ast
import io
import signal
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from utils.file_manager import RESULT_DIR, list_files, read_file

BLOCKED_MODULES = frozenset({
    "os", "subprocess", "sys", "shutil", "importlib",
    "socket", "http", "urllib", "requests", "httpx",
    "pathlib", "glob",
    "pickle", "shelve", "marshal",
    "ctypes", "multiprocessing", "threading",
    "signal", "atexit",
    "code", "codeop", "compileall",
})

BLOCKED_BUILTINS = frozenset({
    "exec", "eval", "compile", "__import__",
    "open", "input", "breakpoint",
    "globals", "locals", "vars",
    "getattr", "setattr", "delattr",
    "memoryview",
})


@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    error: str = ""
    result_df: pd.DataFrame | None = None
    saved_files: list[str] = field(default_factory=list)


def _validate_code(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Syntax error: {e}"]

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            else:
                names = [node.module.split(".")[0]] if node.module else []
            for name in names:
                if name in BLOCKED_MODULES:
                    violations.append(f"Blocked import: {name}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
                violations.append(f"Blocked builtin call: {node.func.id}")
    return violations


def _make_safe_builtins() -> dict:
    import builtins
    safe = {}
    for name in dir(builtins):
        if name not in BLOCKED_BUILTINS and not name.startswith("_"):
            safe[name] = getattr(builtins, name)
    safe["__build_class__"] = builtins.__build_class__
    safe["__name__"] = "__main__"
    return safe


def _make_save_function(
    saved_files: list[str], namespace: dict
) -> callable:
    def save(filename: str, df: pd.DataFrame | None = None):
        if df is None:
            df = namespace.get("result")
        if df is None:
            raise ValueError("No DataFrame to save. Set `result` or pass a DataFrame.")
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df).__name__}")

        name = Path(filename).name
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError("Invalid filename. Use a simple name like 'output.xlsx'.")
        suffix = Path(name).suffix.lower()
        if suffix not in (".xlsx", ".csv"):
            raise ValueError(f"Unsupported format '{suffix}'. Use .xlsx or .csv.")

        dest = RESULT_DIR / name
        if suffix == ".csv":
            df.to_csv(dest, index=False)
        else:
            df.to_excel(dest, index=False)
        saved_files.append(name)

    return save


def load_dataframes() -> dict[str, pd.DataFrame]:
    result = {}
    for fname in list_files():
        df = read_file(fname)
        if df is not None:
            result[fname] = df
    return result


class _Timeout:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self._old_handler = None

    def __enter__(self):
        try:
            self._old_handler = signal.signal(
                signal.SIGALRM, self._handler
            )
            signal.alarm(self.seconds)
        except (ValueError, OSError):
            pass
        return self

    def __exit__(self, *args):
        try:
            signal.alarm(0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)
        except (ValueError, OSError):
            pass

    @staticmethod
    def _handler(signum, frame):
        raise TimeoutError("Code execution timed out.")


def execute(code: str, timeout_seconds: int = 30) -> ExecutionResult:
    violations = _validate_code(code)
    if violations:
        return ExecutionResult(
            success=False,
            error="Code validation failed:\n" + "\n".join(f"  - {v}" for v in violations),
        )

    saved_files: list[str] = []
    files = load_dataframes()

    namespace: dict = {
        "files": files,
        "pd": pd,
        "np": np,
        "result": None,
        "__builtins__": _make_safe_builtins(),
    }
    namespace["save"] = _make_save_function(saved_files, namespace)

    stdout_capture = io.StringIO()
    namespace["print"] = lambda *args, **kwargs: print(
        *args, **kwargs, file=stdout_capture
    )

    try:
        with _Timeout(timeout_seconds):
            exec(compile(code, "<llm_generated>", "exec"), namespace)  # noqa: S102
    except TimeoutError as e:
        return ExecutionResult(
            success=False,
            output=stdout_capture.getvalue(),
            error=str(e),
        )
    except Exception:
        return ExecutionResult(
            success=False,
            output=stdout_capture.getvalue(),
            error=traceback.format_exc(),
        )

    result_df = namespace.get("result")
    if result_df is not None and not isinstance(result_df, pd.DataFrame):
        result_df = None

    return ExecutionResult(
        success=True,
        output=stdout_capture.getvalue(),
        result_df=result_df,
        saved_files=saved_files,
    )
