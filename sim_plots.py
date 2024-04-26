import sys

from dash import Dash, dcc, html

from pdr_dash_plots.callbacks import get_callbacks
from pdr_dash_plots.layout import empty_graphs_template
from pdr_dash_plots.util import get_all_run_names

# TODO: handle clickdata in varimps callback
# TODO: CSS/HTML layout tweaks

app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True
app.layout = html.Div(
    html.Div(
        [
            html.Div(empty_graphs_template, id="live-graphs"),
            dcc.Interval(
                id="interval-component",
                interval=3 * 1000,  # in milliseconds
                n_intervals=0,
                disabled=False,
            ),
        ]
    )
)

get_callbacks(app)

if __name__ == "__main__":
    msg = "USAGE: python sim_plots.py [run_id] [port]"

    if len(sys.argv) > 3:
        print(msg)
        sys.exit(1)

    if len(sys.argv) == 3:
        run_id = sys.argv[1]
        if run_id not in get_all_run_names():
            print("Invalid run_id")
            sys.exit(1)
        port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        run_id = sys.argv[1]
        port = None
        if run_id not in get_all_run_names():
            run_id = None
            port = int(sys.argv[1])
    else:
        run_id = None
        port = 8050

    app.run_id = run_id
    app.run(debug=True, port=port)
