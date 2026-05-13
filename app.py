import re

import streamlit as st

from utils.ollama_client import list_models, chat_stream
from utils.file_manager import (
    save_uploaded, list_files, delete_file, preview_file, get_file_info,
    build_file_context, list_results, delete_result, RESULT_DIR,
)
from utils.export import to_markdown
from utils.code_executor import execute

st.set_page_config(
    page_title="Streamlit AI Lab",
    page_icon="🧪",
    layout="wide",
)

# ── Constants ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a helpful data analysis assistant. You help users work with Excel and CSV files.

When the user asks you to analyze, transform, merge, filter, sort, or perform any operation on uploaded files, you MUST respond with executable Python/pandas code in a ```python code block.

## Rules for code generation:

1. Uploaded files are available as a dictionary called `files` where keys are filenames:
   Example: `files["data.xlsx"]` returns a pandas DataFrame.

2. Available variables and modules:
   - `files`: dict[str, pd.DataFrame] — all uploaded files
   - `pd`: pandas module
   - `np`: numpy module
   - `save(filename)`: save the `result` DataFrame to a downloadable file
   - `save(filename, df)`: save a specific DataFrame

3. Set the variable `result` to the final DataFrame you want to display:
   ```python
   result = merged_df
   ```

4. Call `save("output.xlsx")` to save results as a downloadable file.
   Supported formats: .xlsx, .csv

5. You may use `print()` to show intermediate information.

6. Do NOT use `import` statements — pd and np are already available.

7. Do NOT use `open()`, file I/O, or system commands.

8. When merging files with the same structure, use pd.concat() and groupby().mean() for averaging.

## Response format:
- First, briefly explain what you will do (1-2 sentences).
- Then provide the code in a ```python block.
- After the code block, briefly explain the expected outcome.

If the user asks a general question (not requiring file operations), respond normally without code.\
"""


def extract_code_blocks(text: str) -> list[str]:
    return re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)


# ── Session state init ─────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "execution_results" not in st.session_state:
    st.session_state.execution_results = {}

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Streamlit AI Lab")

    # -- Model selector --
    st.subheader("Model")
    try:
        models = list_models()
    except Exception:
        models = []

    if models:
        selected_model = st.selectbox(
            "Select model",
            models,
            label_visibility="collapsed",
        )
    else:
        st.warning("No models found. Is Ollama running?")
        selected_model = None

    st.divider()

    # -- File upload --
    st.subheader("Files")
    uploaded = st.file_uploader(
        "Upload Excel / CSV",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        for f in uploaded:
            save_uploaded(f)

    # -- File list --
    files = list_files()
    if files:
        for fname in files:
            col_name, col_del = st.columns([4, 1])
            with col_name:
                info = get_file_info(fname)
                if info:
                    st.text(f"📄 {fname} ({info['rows']}r × {info['columns']}c)")
                else:
                    st.text(f"📄 {fname}")
            with col_del:
                if st.button("✕", key=f"del_{fname}"):
                    delete_file(fname)
                    st.rerun()

        # -- File preview --
        preview_target = st.selectbox("Preview file", files, key="preview_select")
        if preview_target:
            df_preview = preview_file(preview_target)
            if df_preview is not None:
                st.dataframe(df_preview, use_container_width=True)
    else:
        st.caption("No files uploaded yet.")

    st.divider()

    # -- Results --
    st.subheader("Results")
    result_files = list_results()
    if result_files:
        for fname in result_files:
            col_name, col_dl, col_del = st.columns([3, 1, 1])
            with col_name:
                st.text(f"📊 {fname}")
            with col_dl:
                fpath = RESULT_DIR / fname
                st.download_button(
                    "⬇",
                    data=fpath.read_bytes(),
                    file_name=fname,
                    key=f"dl_result_{fname}",
                )
            with col_del:
                if st.button("✕", key=f"del_result_{fname}"):
                    delete_result(fname)
                    st.rerun()
    else:
        st.caption("No result files yet.")

    st.divider()

    # -- Actions --
    col_new, col_export = st.columns(2)
    with col_new:
        if st.button("New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.execution_results = {}
            st.rerun()
    with col_export:
        if st.session_state.messages:
            md = to_markdown(st.session_state.messages)
            st.download_button(
                "Export .md",
                data=md,
                file_name="chat_export.md",
                mime="text/markdown",
                use_container_width=True,
            )

# ── Main chat area ─────────────────────────────────────────────────────────────


def _render_code_controls(msg_idx: int, content: str):
    """Show execute button or execution results for an assistant message."""
    exec_result = st.session_state.execution_results.get(msg_idx)

    if exec_result is not None:
        if exec_result.success:
            if exec_result.output:
                st.text(exec_result.output)
            if exec_result.result_df is not None:
                st.dataframe(exec_result.result_df, use_container_width=True)
            for sfname in exec_result.saved_files:
                fpath = RESULT_DIR / sfname
                if fpath.exists():
                    st.download_button(
                        f"⬇ Download {sfname}",
                        data=fpath.read_bytes(),
                        file_name=sfname,
                        key=f"dl_exec_{sfname}_{msg_idx}",
                    )
            st.success("Code executed successfully.")
        else:
            st.error(f"Execution error:\n{exec_result.error}")
        return

    code_blocks = extract_code_blocks(content)
    if code_blocks:
        if st.button("▶ Execute Code", key=f"exec_{msg_idx}"):
            with st.spinner("Executing..."):
                result = execute(code_blocks[0])
            st.session_state.execution_results[msg_idx] = result
            st.rerun()


for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            _render_code_controls(idx, msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not selected_model:
        with st.chat_message("assistant"):
            st.error("No model selected. Please check that Ollama is running.")
    else:
        llm_messages = []
        file_ctx = build_file_context(mode="codegen")
        if file_ctx:
            llm_messages.append({
                "role": "system",
                "content": SYSTEM_PROMPT + "\n\n" + file_ctx,
            })
        else:
            llm_messages.append({
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "The user has no files uploaded. Answer questions normally."
                ),
            })
        llm_messages.extend(st.session_state.messages)

        with st.chat_message("assistant"):
            response = st.write_stream(
                chat_stream(selected_model, llm_messages)
            )
        msg_idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
