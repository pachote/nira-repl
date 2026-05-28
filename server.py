"""
NIRA Persistent REPL MCP
Stateful Python execution environment — variables, imports, and state persist across calls.
"""
import sys
import io
import traceback
import ast
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "NIRA Persistent REPL",
    instructions=(
        "Stateful Python REPL. Variables and imports persist across repl_exec calls. "
        "Use repl_exec to run code, repl_state to inspect current variables, repl_reset to clear. "
        "Matplotlib/PIL outputs are captured as base64 PNG. Install packages with repl_install."
    )
)

# Persistent execution context
_globals: dict = {
    "__builtins__": __builtins__,
    "__name__": "__repl__",
}
_history: list[str] = []


@mcp.tool()
def repl_exec(code: str, timeout_s: int = 30) -> dict:
    """
    Execute Python code in the persistent REPL environment.
    Variables and imports persist between calls.
    Returns: {stdout, stderr, result, error, variables_changed}
    """
    global _globals

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    result = None
    error = None

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_buf
    sys.stderr = stderr_buf

    try:
        # Try to get last expression value
        try:
            tree = ast.parse(code, mode="exec")
            # If last statement is an expression, eval it for its value
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                expr = tree.body.pop()
                exec(compile(tree, "<repl>", "exec"), _globals)
                result = eval(compile(ast.Expression(expr.value), "<repl>", "eval"), _globals)
            else:
                exec(compile(tree, "<repl>", "exec"), _globals)
        except SyntaxError:
            exec(code, _globals)

        _history.append(code)
    except Exception as e:
        error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    stdout = stdout_buf.getvalue()
    stderr = stderr_buf.getvalue()

    # Capture matplotlib figure if one was created
    image_b64 = None
    try:
        import matplotlib.pyplot as plt
        if plt.get_fignums():
            import base64
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            image_b64 = base64.b64encode(buf.read()).decode()
            plt.close("all")
    except ImportError:
        pass

    return {
        "stdout": stdout,
        "stderr": stderr,
        "result": repr(result) if result is not None else None,
        "error": error,
        "image_b64": image_b64,
    }


@mcp.tool()
def repl_state() -> dict:
    """
    Inspect current REPL state — all user-defined variables and their types/values.
    Returns: {variables: {name: {type, repr}}}
    """
    skip = {"__builtins__", "__name__", "__doc__", "__package__", "__loader__", "__spec__"}
    variables = {}
    for k, v in _globals.items():
        if k.startswith("__") or k in skip:
            continue
        try:
            variables[k] = {
                "type": type(v).__name__,
                "repr": repr(v)[:200],
            }
        except Exception:
            variables[k] = {"type": "unknown", "repr": "<unrepresentable>"}
    return {"variables": variables, "history_count": len(_history)}


@mcp.tool()
def repl_reset(keep_imports: bool = True) -> dict:
    """
    Reset the REPL state. keep_imports=True preserves imported modules.
    Returns: {cleared_variables}
    """
    global _globals, _history
    if keep_imports:
        import types
        kept = {k: v for k, v in _globals.items()
                if isinstance(v, types.ModuleType) or k in ("__builtins__", "__name__")}
        cleared = [k for k in _globals if k not in kept]
        _globals = kept
    else:
        cleared = [k for k in _globals if k not in ("__builtins__", "__name__")]
        _globals = {"__builtins__": __builtins__, "__name__": "__repl__"}
    _history.clear()
    return {"cleared_variables": cleared}


@mcp.tool()
def repl_install(package: str) -> dict:
    """
    Install a Python package into the current environment.
    Returns: {success, output}
    """
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True, text=True, timeout=120
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout[-2000:] + result.stderr[-500:],
    }


@mcp.tool()
def repl_history(last_n: int = 10) -> dict:
    """Return recent execution history."""
    return {"history": _history[-last_n:], "total": len(_history)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
