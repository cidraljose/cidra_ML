import base64
import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def fig_to_base64(fig):
    """Converts a matplotlib figure to a base64 encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return img_str


def create_correlation_heatmap(df, numerical_cols):
    """Generates a correlation heatmap for numerical columns."""
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_matrix = df[numerical_cols].corr()
    corr_matrix = corr_matrix.where(
        pd.DataFrame(
            np.tril(np.ones(corr_matrix.shape)),
            index=corr_matrix.index,
            columns=corr_matrix.columns,
        ).astype(bool)
    )
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        ax=ax,
    )
    return fig_to_base64(fig)


def create_countplot(df, column):
    """Generates a count plot for a given categorical column."""
    fig, ax = plt.subplots()
    sns.countplot(x=df[column], ax=ax, order=df[column].value_counts().index)
    ax.yaxis.set_label_text("Count")
    ax.xaxis.set_label_text("Type")
    ax.set_xticklabels(
        ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
    )
    fig.tight_layout()
    return fig_to_base64(fig)


def create_histogram(df, column):
    """Generates a histogram for a given column."""
    fig, ax = plt.subplots()
    sns.histplot(df[column], kde=True, ax=ax)
    ax.yaxis.set_label_text("Density")
    return fig_to_base64(fig)


def create_normalized_pdf_plot(df, numerical_cols):
    """
    Generates a single plot with PDF/KDE for all numerical columns.
    Each column's values are scaled using MinMax Scaler.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.get_cmap("viridis")(np.linspace(0, 1, len(numerical_cols)))

    for i, col in enumerate(numerical_cols):
        data = df[col]
        scaled_data = (data - data.min()) / (data.max() - data.min())
        sns.kdeplot(
            data=scaled_data,
            ax=ax,
            label=f"{col}",
            color=colors[i],
            fill=True,
            alpha=0.5,
            linewidth=0,
        )
    ax.legend()
    ax.set_xlabel("Value (MinMax scaled)")
    ax.set_ylabel("Density")
    return fig_to_base64(fig)


def create_missing_values_plot(df):
    """Generates a bar plot showing the count of missing values for each column."""
    missing_values = df.isnull().sum()
    missing_values = missing_values[missing_values > 0]

    if missing_values.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 3))
    missing_values.sort_values(ascending=False).plot(kind="bar", ax=ax)
    ax.set_title("")
    ax.set_xlabel("Features")
    ax.set_ylabel("Number of Missing Values")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig_to_base64(fig)
