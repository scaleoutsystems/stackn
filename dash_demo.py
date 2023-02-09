import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import requests
from apps.models import AppInstance, Apps
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
from projects.models import Project

app = DjangoDash("FEDnDashboard")


menu = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        dbc.Select(
                                            id="reducer-select",
                                            options=[],
                                            className="form-control",
                                        )
                                    ]
                                )
                            ]
                        )
                    ],
                    className="col-4",
                ),
                dbc.Col(id="reducer-state", className="col-2"),
            ]
        ),
        dbc.Row(id="submenu"),
    ]
)

main = dbc.Row(
    [
        dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Combiners", className="card-title"),
                                dbc.Table(
                                    [
                                        html.Thead(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Th("Name"),
                                                        html.Th(
                                                            "Active Clients"
                                                        ),
                                                        html.Th("IP"),
                                                        html.Th("Country"),
                                                        html.Th("Region"),
                                                        html.Th("City"),
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Tbody(
                                            [], id="combiner-info-table"
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4("Round Time", className="card-title"),
                                dcc.Graph(id="combiners-round-plot"),
                            ]
                        )
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Combiner Load", className="card-title"
                                ),
                                dcc.Graph(id="combiners-combiner-plot"),
                            ]
                        )
                    ]
                ),
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Controller MEM and CPU Monitoring",
                                    className="card-title",
                                ),
                                dcc.Graph(id="combiners-memcpu-plot"),
                            ]
                        )
                    ]
                ),
            ]
        )
    ]
)

app.layout = html.Div([menu, main])


@app.callback(
    Output(component_id="combiner-info-table", component_property="children"),
    Output(component_id="combiners-round-plot", component_property="figure"),
    Output(
        component_id="combiners-combiner-plot", component_property="figure"
    ),
    Output(component_id="combiners-memcpu-plot", component_property="figure"),
    Output(component_id="reducer-state", component_property="children"),
    Output(component_id="reducer-select", component_property="options"),
    Input(component_id="reducer-select", component_property="value"),
)
def reducer_select(red_select, request):

    if "current_project" in request.session:
        project_slug = request.session["current_project"]
    else:
        raise PreventUpdate()
    reducer_app = Apps.objects.get(slug="reducer")
    this_project = Project.objects.get(slug=project_slug)
    reducers = AppInstance.objects.filter(
        app=reducer_app, project=this_project
    )
    options = []
    for reducer in reducers:
        options.append({"label": reducer.name, "value": str(reducer.pk)})

    combiners_info = []
    roundplot = {}
    combinerplot = {}
    memcpuplot = {}
    state = ""
    if red_select is not None:
        # TODO: Check that user has access to project.
        sel_reducer = AppInstance.objects.get(
            pk=red_select, project__slug=project_slug
        )
        reducer_params = sel_reducer.parameters
        r_host = reducer_params["release"]
        r_domain = reducer_params["global"]["domain"]

        try:
            url = "https://{}.{}/api/state".format(r_host, r_domain)
            res = requests.get(url, verify=False)
            current_state = res.json()["state"]
        except Exception as err:
            print(err)
        state = dbc.Card([dbc.CardBody(current_state)])

        try:
            url = "https://{}.{}/api/combiners/info".format(r_host, r_domain)
            print(url)
            res = requests.get(url, verify=False)
            combiners_raw = res.json()
        except Exception as err:
            print(err)

        for combiner_raw in combiners_raw:
            row = [
                html.Td(combiner_raw["name"]),
                html.Td(combiner_raw["nr_active_clients"]),
                html.Td(combiner_raw["ip"]),
                html.Td(combiner_raw["country"]),
                html.Td(combiner_raw["region"]),
                html.Td(combiner_raw["city"]),
            ]
            combiners_info.append(html.Tr(row))

        try:
            url = "https://{}.{}/api/combiners/roundplot".format(
                r_host, r_domain
            )
            print(url)
            res = requests.get(url, verify=False)
            roundplot = res.json()
        except Exception as err:
            print(err)

        try:
            url = "https://{}.{}/api/combiners/combinerplot".format(
                r_host, r_domain
            )
            print(url)
            res = requests.get(url, verify=False)
            combinerplot = res.json()
        except Exception as err:
            print(err)

        try:
            url = "https://{}.{}/api/combiners/memcpuplot".format(
                r_host, r_domain
            )
            print(url)
            res = requests.get(url, verify=False)
            memcpuplot = res.json()
        except Exception as err:
            print(err)

    return combiners_info, roundplot, combinerplot, memcpuplot, state, options
