import plotly.express as px
import plotly.io as pio


def create_boxplot(df, column):
    """Generates a box plot for a given column."""
    fig = px.box(df, y=column, title=f"Box Plot of {column}")
    return pio.to_json(fig)


def create_correlation_heatmap(df, numerical_cols):
    """Generates a correlation heatmap for numerical columns."""
    corr_matrix = df[numerical_cols].corr()
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap",
    )
    return pio.to_json(fig)


def create_countplot(df, column):
    """Generates a count plot for a given categorical column."""
    fig = px.bar(
        df[column].value_counts().reset_index(),
        x="index",
        y=column,
        title=f"Count of {column}",
        labels={"index": column, column: "Count"},
    )
    return pio.to_json(fig)


def create_histogram(df, column):
    """Generates a histogram for a given column."""
    fig = px.histogram(df, x=column, title=f"Distribution of {column}")
    return pio.to_json(fig)


def create_pairplot(df, numerical_cols, color_col=None):
    """Generates a pair plot for numerical columns, optionally colored by a categorical column."""
    if color_col and color_col in df.columns and df[color_col].dtype == "object":
        fig = px.scatter_matrix(
            df,
            dimensions=numerical_cols,
            color=color_col,
            title=f"Pair Plot colored by {color_col}",
        )
    else:
        fig = px.scatter_matrix(df, dimensions=numerical_cols, title="Pair Plot")
    return pio.to_json(fig)


def create_scatter_matrix(df, numerical_cols):
    """Generates a scatter matrix for numerical columns."""
    fig = px.scatter_matrix(df, dimensions=numerical_cols, title="Scatter Matrix")
    return pio.to_json(fig)
