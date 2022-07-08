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
    )

    for trx_type in trx.order_by().values_list("trx_type", flat=True).distinct():
        trx_subset = trx.filter(trx_type=trx_type)

        # create custom_data array
        trx_ids = [x.id for x in trx_subset]
        record_ids = [str(x.record_id) for x in trx_subset]  # str to handle nulls
        trx_types = [x.trx_type for x in trx_subset]

        fig.add_trace(
            go.Scatter(
                x=[x.trx_date for x in trx_subset],
                y=[x.credit_saldo for x in trx_subset],
                mode="markers",
                marker={"color": color_dict[trx_type]},
                name=trx_type,
                customdata=list(zip(trx_ids, record_ids, trx_types)),
                hovertemplate="%{x}<br>"
                + "Saldo: %{y}<br>"
                + "Trx Id: %{customdata[0]}<br>"
                + "Record Id: %{customdata[1]}<br>"
                + "<extra>%{customdata[2]}</extra>",
            )
        )

    return fig.to_html()
