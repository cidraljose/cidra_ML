import base64
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.io as pio


def create_predicted_vs_real_plot(y_true, y_pred):
    """
    Generates a scatter plot of predicted vs. real values.

    Args:
        y_true (pd.Series): The actual target values.
        y_pred (pd.Series): The values predicted by the model.

    Returns:
        str: A base64 encoded string of the plot image, or None if data is not numeric.
    """
    # Ensure data is numeric for plotting
    if not pd.api.types.is_numeric_dtype(y_true) or not pd.api.types.is_numeric_dtype(
        y_pred
    ):
        return None

    fig = px.scatter(
        x=y_true, y=y_pred, labels={"x": "Real Values", "y": "Predicted Values"}
    )
    # Add a line for perfect predictions
    fig.add_shape(
        type="line",
        x0=y_true.min(),
        y0=y_true.min(),
        x1=y_true.max(),
        y1=y_true.max(),
        line=dict(color="Red", dash="dash"),
    )
    fig.update_layout(title="Predicted vs. Real Values", showlegend=False)

    buffer = BytesIO()
    pio.write_image(fig, buffer, format="png")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
