from dash import Dash, ClientsideFunction
import json
import inspect
import textwrap
from functools import wraps
import uuid
from typing import Any
import time
import os


PYSCRIPT_TYPE = ["py", "mpy", "py-game"]
PYSCRIPT_VERSION = "2025.5.1"
PYSCALLBACK_JS_FILENAME = "__pyscallback.js"

pys_callback_functions: list[str] = []
pys_add_scripts: dict[str, Any] = {}
pys_add_codes: dict[str, Any] = {}


def pys_set_callback(app: Dash, config: dict[str, Any], *args) -> None:
    global pys_callback_functions, pys_add_scripts

    funcname = config.get("func", None)
    if not isinstance(funcname, str):
        raise ValueError(
            "The 'func' key in config must be a string representing the function name."
        )

    script = config.get("script", None)
    if not isinstance(script, str):
        raise ValueError(
            "The 'script' key in config must be a string representing the script path."
        )

    pys_type = config.get("type", "mpy")
    if pys_type not in PYSCRIPT_TYPE:
        raise ValueError(
            f"Invalid pyscript type: {pys_type}. Supported types are: {PYSCRIPT_TYPE}"
        )

    no_cache = config.get("nocache", True)
    if no_cache:
        cache_str = f"?m={time.time()}"
    else:
        cache_str = ""

    if "func" in config:
        config.pop("func")
    if "script" in config:
        config.pop("script")
    if "type" in config:
        config.pop("type")
    if "nocache" in config:
        config.pop("nocache")

    config_str = json.dumps(config, ensure_ascii=False)

    pys_callback_functions.append(funcname)

    pys_add_scripts[script] = {
        "scr": script + cache_str,
        "config": config_str,
        "type": pys_type,
    }

    app.clientside_callback(
        ClientsideFunction(namespace="pyscallback", function_name=funcname),
        *args,
    )


def pys_callback(app: Dash, config: dict[str, Any], *args) -> Any:
    def extract_source_without_decorators(func):
        original = inspect.unwrap(func)
        source = inspect.getsource(original)
        lines = source.splitlines()

        def_line_index = next(
            i for i, line in enumerate(lines) if line.strip().startswith("def ")
        )
        lines_without_decorators = lines[def_line_index:]

        return textwrap.dedent("\n".join(lines_without_decorators)), original.__name__

    def func_decorator(func):
        @wraps(func)
        def wrapper():
            global pys_callback_functions, pys_add_codes
            pys_type = config.get("type", "mpy")
            if pys_type not in PYSCRIPT_TYPE:
                raise ValueError(
                    f"Invalid pyscript type: {pys_type}. Supported types are: {PYSCRIPT_TYPE}"
                )

            code_id = str(uuid.uuid4())

            code, funcname = extract_source_without_decorators(func)

            code += f"""\n\nimport js\nfrom pyscript.ffi import create_proxy\njs.pys.setCallback("{funcname}", create_proxy({funcname}))\n"""

            code = code.replace("\\", "\\\\").replace("\n", "\\n")

            if "type" in config:
                config.pop("type")

            config_str = json.dumps(config, ensure_ascii=False)

            pys_callback_functions.append(funcname)
            pys_add_codes[code_id] = {
                "code": code,
                "config": config_str,
                "type": pys_type,
            }

            app.clientside_callback(
                ClientsideFunction(namespace="pyscallback", function_name=funcname),
                *args,
            )

        return wrapper()

    return func_decorator


def pys_start(debug: bool = True, assets: str = "assets") -> None:

    global pys_callback_functions, pys_add_scripts, pys_add_codes

    if not isinstance(assets, str):
        raise ValueError(
            "The 'assets' parameter must be a string representing the assets directory."
        )

    assets_path = os.path.join(os.getcwd(), assets)
    pys_callback_js_filename = os.path.join(assets_path, PYSCALLBACK_JS_FILENAME)

    if not debug and os.path.exists(pys_callback_js_filename):
        return

    scriptscode = ""
    for details in pys_add_scripts.values():
        scriptscode += f"""    globalThis.pys.addScript("{details['scr']}", `{details['config']}`, "{details['type']}");\n"""

    codescode = ""
    for codeid, details in pys_add_codes.items():
        codescode += f"""    globalThis.pys.addScriptCode(`{details['code']}`, "{codeid}", `{details['config']}`, "{details['type']}");\n"""

    funcscode = ""
    for function in pys_callback_functions:
        funcscode += f"""    globalThis.pys.registerFunction("{function}");\n"""

    javascript_code = f"""
class PysCallback {{
    static #promises = new Map();
    static #callbacks = new Map();
    static #srcs = new Array();
    static #codeids = new Array();
    static #pystypes = {json.dumps(PYSCRIPT_TYPE)};
    static #pysversion = "{PYSCRIPT_VERSION}";

    static #createPromise(funcname) {{
        if (!PysCallback.#promises.has(funcname)) {{
            let resolve;
            const promise = new Promise((res) => resolve = res);
            PysCallback.#promises.set(funcname, {{ promise, resolve }});
        }}
    }}

    static initPyScript() {{
        let script = document.createElement("script");
        script.src = `https://pyscript.net/releases/${{PysCallback.#pysversion}}/core.js`;
        script.type = "module";

        let css = document.createElement("link");
        css.href = `https://pyscript.net/releases/${{PysCallback.#pysversion}}/core.css`;
        css.rel = "stylesheet";

        document.head.appendChild(script);
        document.head.appendChild(css);
    }}

    static addScript(src, config, type = "mpy") {{
        if (PysCallback.#srcs.includes(src)) return;

        if (!PysCallback.#pystypes.includes(type)) {{
            throw new Error(`Invalid type: ${{type}}. Supported types are: ${{PysCallback.#pystypes.join(", ")}}`);
        }}

        const script = document.createElement("script");
        script.src = src;
        script.type = type;

        if (typeof config === "object") {{
            script.config = JSON.stringify(config);
        }} else if (typeof config === "string") {{
            script.config = config;
        }}

        document.head.appendChild(script);
    }}

    static addScriptCode(code, codeid, config, type = "mpy") {{
        if (PysCallback.#codeids.includes(codeid)) return;

        if (!PysCallback.#pystypes.includes(type)) {{
            throw new Error(`Invalid type: ${{type}}. Supported types are: ${{PysCallback.#pystypes.join(", ")}}`);
        }}

        const script = document.createElement("script");
        script.textContent = code;
        script.type = type;

        if (typeof config === "object") {{
            script.config = JSON.stringify(config);
        }} else if (typeof config === "string") {{
            script.config = config;
        }}

        document.body.appendChild(script);

        PysCallback.#codeids.push(codeid);
    }}

    static registerFunction(funcnames) {{
        if (!Array.isArray(funcnames)) {{
            funcnames = [funcnames];
        }}

        for (const funcname of funcnames) {{
            globalThis.dash_clientside.pyscallback[funcname] = async (...args) => {{
                return await PysCallback.call(funcname, ...args);
            }};
        }}
    }}

    static setCallback(funcname, callback) {{
        if (!PysCallback.#promises.has(funcname)) {{
            PysCallback.#createPromise(funcname);
        }}
        if (!PysCallback.#callbacks.has(funcname)) {{
            PysCallback.#callbacks.set(funcname, callback);
        }}
        PysCallback.#resolve(funcname);
    }}

    static hasCallback(funcname) {{
        return PysCallback.#callbacks.has(funcname);
    }}

    static async call(funcname, ...args) {{
        if (!PysCallback.#promises.has(funcname)) {{
            PysCallback.#createPromise(funcname);
        }}

        await PysCallback.#wait(funcname);

        if (PysCallback.#callbacks.has(funcname)) {{
            const callback = PysCallback.#callbacks.get(funcname);
            return await callback.call(null, ...args);
        }}
    }}

    static #resolve(funcname) {{
        if (PysCallback.#promises.has(funcname)) {{
            const {{ resolve }} = PysCallback.#promises.get(funcname);
            resolve();
        }}
    }}

    static async #wait(funcname) {{
        if (!PysCallback.#promises.has(funcname)) {{
            PysCallback.#createPromise(funcname);
        }}
        const {{ promise }} = PysCallback.#promises.get(funcname);
        await promise;
    }}
}}

globalThis.pys = PysCallback;
globalThis.dash_clientside = globalThis.dash_clientside || {{}};
globalThis.dash_clientside.pyscallback = globalThis.dash_clientside.pyscallback || {{}};

pys.initPyScript();

globalThis.addEventListener("DOMContentLoaded", () => {{
{scriptscode}{codescode}{funcscode}}});
"""

    if not os.path.exists(assets_path):
        os.makedirs(assets_path)

    with open(pys_callback_js_filename, "w", encoding="utf-8") as f:
        f.write(javascript_code)
