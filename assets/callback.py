import js  # type: ignore
from pyscript.ffi import create_proxy  # type: ignore


def update_output2(value):
    return f"選択された値: {value}です!!!"


js.dash_clientside.pyscallback.setCallback("update_output2", create_proxy(update_output2))
