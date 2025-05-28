import js  # type: ignore
from pyscript.ffi import create_proxy  # type: ignore


def update_output2(value):
    return f"選択された値: {value}です!!!"


js.pys.setCallback("update_output2", create_proxy(update_output2))
