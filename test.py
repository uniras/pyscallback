# %%
import dash
from dash import dcc, html, Input, Output
from pyscallback import pys_set_callback, pys_callback, pys_start

# アプリケーションの初期化
app = dash.Dash()


# レイアウトの定義
app.layout = html.Div(
    [
        html.H1("スライダーで数値を変更"),
        dcc.Slider(
            id="my-slider",
            min=0,
            max=100,
            step=1,
            value=50,
            marks={i: str(i) for i in range(0, 101, 10)},
        ),
        html.Div(id="slider-output-container"),
        dcc.Slider(
            id="my-slider-2",
            min=0,
            max=100,
            step=1,
            value=50,
            marks={i: str(i) for i in range(0, 101, 10)},
        ),
        html.Div(id="slider-output-container-2"),
    ]
)

# コールバックとなるPyScriptコードを直接記述する
@pys_callback(
    app,
    {"type": "mpy"},
    Output("slider-output-container", "children"),
    Input("my-slider", "value"),
)
def update_output(value):
    return f"選択された値: {value}ですよ!"


# 別ファイルで記述したPyScriptコードを使用する
pys_set_callback(
    app,
    {"func": "update_output2", "script": "/assets/callback.py", "type": "mpy"},
    Output("slider-output-container-2", "children"),
    Input("my-slider-2", "value"),
)

# pys_callbackを使用するためにrun直前にこの関数を呼び出す
pys_start()

# サーバー起動
if __name__ == "__main__":
    app.run(debug=True, dev_tools_hot_reload_interval=1)
# %%
