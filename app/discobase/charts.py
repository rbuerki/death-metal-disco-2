import plotly.graph_objects as go
import plotly.io as pio

pio.templates.default = "simple_white"


def make_trxcredit_chart(trx):
    min_date = trx.order_by("trx_date").first().trx_date
    max_date = trx.order_by("trx_date").last().trx_date
    color_dict = {"Addition": "green", "Removal": "red", "Purchase": "blue"}

    fig = go.Figure(
        data=go.Scatter(
            x=[x.trx_date for x in trx],
            y=[x.credit_saldo for x in trx],
            mode="lines",
            line={"color": "lightgray"},
            showlegend=False,
        )
    )

    fig.update_layout(
        title=f"Credit Saldo Movement, {min_date} to {max_date}",
        xaxis_title="Date",
        yaxis_title="Credit Saldo",
        legend_title="Trx Types",
        #     font={
        #         family: "Courier New, monospace",
        #         size: 18,
        #         color: "RebeccaPurple"
        #     }
    )

    for trx_type in trx.order_by().values_list("trx_type", flat=True).distinct():
        trx_subset = trx.filter(trx_type=trx_type)

        fig.add_trace(
            go.Scatter(
                x=[x.trx_date for x in trx_subset],
                y=[x.credit_saldo for x in trx_subset],
                mode="markers",
                marker={"color": color_dict[trx_type]},
                name=trx_type,
            )
        )

    return fig.to_html()
