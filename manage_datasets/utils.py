import base64
import io

import matplotlib.pyplot as plt
import seaborn as sns


def fig_to_base64(fig):
    """Converts a matplotlib figure to a base64 encoded PNG string."""
    buf = io.BytesIO()
    # Use bbox_inches='tight' to prevent labels from being cut off
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)  # Close the figure to free up memory
    return img_str


def create_boxplot(df, column):
    """Generates a box plot for a given column."""
    fig, ax = plt.subplots()
    sns.boxplot(y=df[column], ax=ax)
    ax.set_title(f"Box Plot of {column}")
    return fig_to_base64(fig)


def create_correlation_heatmap(df, numerical_cols):
    """Generates a correlation heatmap for numerical columns."""
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_matrix = df[numerical_cols].corr()
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        ax=ax,
    )
    ax.set_title("Correlation Heatmap")
    return fig_to_base64(fig)


def create_countplot(df, column):
    """Generates a count plot for a given categorical column."""
    fig, ax = plt.subplots()
    sns.countplot(y=df[column], ax=ax, order=df[column].value_counts().index)
    ax.set_title(f"Count of {column}")
    return fig_to_base64(fig)


def create_histogram(df, column):
    """Generates a histogram for a given column."""
    fig, ax = plt.subplots()
    sns.histplot(df[column], kde=True, ax=ax)
    ax.set_title(f"Distribution of {column}")
    return fig_to_base64(fig)


def create_pairplot(df, numerical_cols, color_col=None):
    """Generates a pair plot for numerical columns, optionally colored by a categorical column."""
    hue = None
    if color_col and color_col in df.columns and df[color_col].dtype == "object":
        hue = color_col

    pair_plot = sns.pairplot(df, vars=numerical_cols, hue=hue)
    pair_plot.fig.suptitle(
        f"Pair Plot colored by {color_col}" if hue else "Pair Plot", y=1.02
    )
    # sns.pairplot returns a PairGrid object, not a figure. We access the figure via .fig
    return fig_to_base64(pair_plot.fig)


def create_scatter_matrix(df, numerical_cols):
    """Generates a scatter matrix for numerical columns."""
    # In seaborn, a scatter matrix is typically called a pairplot.
    pair_plot = sns.pairplot(df[numerical_cols])
    pair_plot.fig.suptitle("Scatter Matrix", y=1.02)
    return fig_to_base64(pair_plot.fig)
