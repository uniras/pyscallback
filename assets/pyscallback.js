
class PysCallback {
    static #promises = new Map();
    static #callbacks = new Map();
    static #srcs = new Array();
    static #codeids = new Array();
    static #pystypes = ["py", "mpy", "py-game"];
    static #pysversion = "2025.5.1";

    static #createPromise(funcname) {
        if (!PysCallback.#promises.has(funcname)) {
            let resolve;
            const promise = new Promise((res) => resolve = res);
            PysCallback.#promises.set(funcname, { promise, resolve });
        }
    }

    static initPyScript() {
        let script = document.createElement("script");
        script.src = `https://pyscript.net/releases/${PysCallback.#pysversion}/core.js`;
        script.type = "module";

        let css = document.createElement("link");
        css.href = `https://pyscript.net/releases/${PysCallback.#pysversion}/core.css`;
        css.rel = "stylesheet";

        document.head.appendChild(script);
        document.head.appendChild(css);
    }

    static addScript(src, config, type = "mpy") {
        if (PysCallback.#srcs.includes(src)) return;

        if (!PysCallback.#pystypes.includes(type)) {
            throw new Error(`Invalid type: ${type}. Supported types are: ${PysCallback.#pystypes.join(", ")}`);
        }

        const script = document.createElement("script");
        script.src = src;
        script.type = type;

        if (typeof config === "object") {
            script.config = JSON.stringify(config);
        } else if (typeof config === "string") {
            script.config = config;
        }

        document.head.appendChild(script);
    }

    static addScriptCode(code, codeid, config, type = "mpy") {
        if (PysCallback.#codeids.includes(codeid)) return;

        if (!PysCallback.#pystypes.includes(type)) {
            throw new Error(`Invalid type: ${type}. Supported types are: ${PysCallback.#pystypes.join(", ")}`);
        }

        const script = document.createElement("script");
        script.textContent = code;
        script.type = type;

        if (typeof config === "object") {
            script.config = JSON.stringify(config);
        } else if (typeof config === "string") {
            script.config = config;
        }

        document.body.appendChild(script);

        PysCallback.#codeids.push(codeid);
    }

    static registerFunction(funcnames) {
        if (!Array.isArray(funcnames)) {
            funcnames = [funcnames];
        }

        for (const funcname of funcnames) {
            globalThis.dash_clientside.pyscallback[funcname] = async (...args) => {
                return await PysCallback.call(funcname, ...args);
            };
        }
    }

    static setCallback(funcname, callback) {
        if (!PysCallback.#promises.has(funcname)) {
            PysCallback.#createPromise(funcname);
        }
        if (!PysCallback.#callbacks.has(funcname)) {
            PysCallback.#callbacks.set(funcname, callback);
        }
        PysCallback.#resolve(funcname);
    }

    static hasCallback(funcname) {
        return PysCallback.#callbacks.has(funcname);
    }

    static async call(funcname, ...args) {
        if (!PysCallback.#promises.has(funcname)) {
            PysCallback.#createPromise(funcname);
        }

        await PysCallback.#wait(funcname);

        if (PysCallback.#callbacks.has(funcname)) {
            const callback = PysCallback.#callbacks.get(funcname);
            return await callback.call(null, ...args);
        }
    }

    static #resolve(funcname) {
        if (PysCallback.#promises.has(funcname)) {
            const { resolve } = PysCallback.#promises.get(funcname);
            resolve();
        }
    }

    static async #wait(funcname) {
        if (!PysCallback.#promises.has(funcname)) {
            PysCallback.#createPromise(funcname);
        }
        const { promise } = PysCallback.#promises.get(funcname);
        await promise;
    }
}

globalThis.pys = PysCallback;
globalThis.dash_clientside = globalThis.dash_clientside || {};
globalThis.dash_clientside.pyscallback = globalThis.dash_clientside.pyscallback || {};

pys.initPyScript();

globalThis.addEventListener("DOMContentLoaded", () => {
    globalThis.pys.addScript("/assets/callback.py?m=1748158818.9522042", `{}`, "mpy");
    globalThis.pys.addScriptCode(`def update_output(value):\n    return f"選択された値: {value}ですよ!"\n\nimport js\nfrom pyscript.ffi import create_proxy\njs.pys.setCallback("update_output", create_proxy(update_output))\n`, "a9667a8b-0a09-473d-8cdc-6df34f9c3e87", `{}`, "mpy");
    globalThis.pys.registerFunction("update_output");
    globalThis.pys.registerFunction("update_output2");
});
