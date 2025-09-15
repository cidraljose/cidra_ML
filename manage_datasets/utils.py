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


def create_boxplot(df, column):
    """Generates a box plot for a given column."""
    fig, ax = plt.subplots()
    sns.boxplot(y=df[column], ax=ax)
    return fig_to_base64(fig)


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
    ax.yaxis.set_label_text("Quantidade")
    ax.xaxis.set_label_text("Tipo")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig_to_base64(fig)


def create_histogram(df, column):
    """Generates a histogram for a given column."""
    fig, ax = plt.subplots()
    sns.histplot(df[column], kde=True, ax=ax)
    ax.yaxis.set_label_text("Densidade de valores")
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
    return fig_to_base64(pair_plot.fig)


def create_scatter_matrix(df, numerical_cols):
    """Generates a scatter matrix for numerical columns."""
    pair_plot = sns.pairplot(df[numerical_cols])
    pair_plot.fig.suptitle("Scatter Matrix", y=1.02)
    return fig_to_base64(pair_plot.fig)


def create_pdf_plot(df, numerical_cols):
    """Generates a single plot with PDF/KDE for all numerical columns."""
    fig, ax = plt.subplots(figsize=(12, 7))
    for col in numerical_cols:
        sns.kdeplot(df[col], ax=ax, label=col, fill=True, alpha=0.2)
    ax.legend()
    return fig_to_base64(fig)


def create_normalized_pdf_plot(df, numerical_cols):
    """Generates a single plot with PDF/KDE for all numerical columns after normalization."""
    fig, ax = plt.subplots(figsize=(12, 7))
    for col in numerical_cols:
        normalized_data = (df[col] - df[col].mean()) / df[col].std()
        sns.kdeplot(
            normalized_data, ax=ax, label=f"{col} (Normalized)", fill=True, alpha=0.2
        )
    ax.legend()
    return fig_to_base64(fig)
