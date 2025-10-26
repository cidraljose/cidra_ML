# Cidra-ML 🍋

Cidra-ML is a user-friendly web application designed to simplify the machine learning workflow, from data management to model training and prediction. It leverages the power of **AutoGluon**, a leading AutoML library, to allow users to build high-quality regression models with minimal effort.

The platform provides an intuitive interface for users to upload and manage their datasets, train new models, evaluate their performance, and use them to make predictions.

## About the application features

### 1. User Authentication

- **Registration & Login:** A authentication system ensures that each user has a private workspace.
- **Data Isolation:** All datasets, models, and results are tied to the logged-in user, preventing unauthorized access.

### 2. Dataset Management

- **CSV Upload:** Upload datasets in CSV format.
- **Data Visualization:** Generate and view plots and statistics for any dataset, including:
  - Descriptive statistics and data types.
  - Missing value analysis.
  - Histograms and normalized PDF plots for numerical features.
  - Correlation heatmaps.
  - Count plots for categorical features.
- **Data Manipulation:**
  - **Split:** Divide a dataset into training and testing sets with a user-defined ratio.
  - **Merge:** Combine multiple datasets into a single new dataset.

### 3. Model Training & Management

- **Asynchronous Training:** Model training is offloaded to a **Celery** background worker. This means you can start a long training job and continue to use the application or even close the browser tab. The UI provides live status updates (`TRAINING`, `COMPLETED`, `FAILED`).
- **AutoGluon Integration:** Train regression models by selecting a dataset, a target column, and training parameters. AutoGluon handles the rest, from feature engineering to model selection and hyperparameter tuning.
- **Upload Existing Models:** Upload pre-trained AutoGluon models packaged as `.zip` files.
- **Model Details:** View details for each model, including its description, models, features, target variable and training duration.

### 4. Model Evaluation (Testing)

- **Asynchronous Evaluation:** Similar to training, model evaluation is a background task handled by Celery, keeping the UI responsive.
- **Performance Metrics:** Evaluate a model's performance on a test dataset to get regression metrics.
- **Rich Visualization:** For each test result, you can visualize:
  - A scatter plot of **Predicted vs. Real Values**.
  - The detailed **AutoGluon Leaderboard**, showing the performance of all the individual models within the trained stack.

### 5. Prediction Engine

- **Asynchronous Prediction:** Predictions on large datasets are also handled by Celery workers.
- **Batch Prediction:** Select a model and a dataset to generate predictions for every row in the file. The results, including the original data and the new prediction column, can be downloaded as a CSV.
- **Manual Prediction:** Interactively make predictions for one or more data rows by manually entering feature values.
- **Prediction Visualization:** Generate 2D or 3D scatter plots to explore the relationship between input features and the resulting predictions.

## How It Works

### Backend

- **Python:** The core programming language.
- **Django:** A high-level web framework used to structure the application, manage the database, and handle user requests.
- **AutoGluon:** The core AutoML library that powers the model training, evaluation, and prediction capabilities.
- **Celery:** A distributed task queue that manages background jobs. This is essential for offloading long-running processes like `predictor.fit()` and `predictor.predict()`, ensuring the web application remains fast and responsive.
- **Pandas:** Used for data manipulation, reading CSVs, and preparing data for AutoGluon.
- **Matplotlib & Seaborn:** Python libraries used to generate static plots within the Celery background tasks. These plots are then encoded and sent to the frontend.
- **SQLite:** Used as the primary database for storing application data (users, model metadata, etc.) and as the message broker for Celery in the development environment.

### Frontend

- **HTML5 & CSS3:** The standard for structuring and styling the web pages.
- **Bootstrap 5:** A CSS framework used for creating a user interface. It provides components like modals, tabs, forms, and the navigation bar.
- **JavaScript:** Used to create a dynamic and interactive user experience. Key functionalities include:
  - **AJAX with `fetch`:** Asynchronously fetching data from the backend without reloading the page. This is used to dynamically populate form fields (e.g., loading a dataset's columns when a user selects it).
  - **DOM Manipulation:** Dynamically creating and updating HTML elements, such as the forms for manual prediction or the content of visualization modals.
  - **Live Polling:** Periodically sending requests to the backend to check the status of running Celery tasks (`TRAINING`, `RUNNING`, etc.) and updating the UI in real-time to reflect the progress.

## Project Structure

The project is organized into several Django apps, each with a specific responsibility:

- `cidra_ML/`: The main project directory containing global settings and URL configurations.
- `users/`: Manages user authentication, including registration, login, and logout.
- `manage_datasets/`: Handles all logic related to uploading, visualizing, splitting, and merging datasets.
- `manage_MLmodels/`: Manages model training, uploading, and the detailed model visualization modal.
- `testing/`: Contains the views, tasks, and models for evaluating model performance.
- `predicting/`: Contains the views, tasks, and models for making predictions.
- `templates/`: A central directory for all HTML templates, including the base layout and partials for reusable components.

## Getting Started: Access onlinelink

<Insert link here>

## Getting Started: Running Locally

If you prefeer to run the project locally, follow these steps to set up and run the project on your local machine.

_Note: These steps were done on Windows. For other operational systems, it will be necessary to adapt the following commands._

### Prerequisites

- Python 3.8+

### 1. Clone the Repository

If you have Git installed on your machine, clone the repository using the following command:

```bash
git clone https://github.com/cidraljose/cidra_ML.git
cd cidra_ML
```

Otherwise, you can just download the project as a zip file and extract it.

### 2. Set Up a Virtual Environment (Optional)

Open a `CMD` terminal inside the project directory and run the following commands.

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

Install all the required Python libs.

```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations

This command will set up the SQLite database with the necessary tables, synchronizing the database structures with the models defined in the project.

```bash
python manage.py migrate
```

### 5. Run the Application

You will need to run two processes in separate terminals.

**Terminal 1: Start the Django Development Server**

```bash
python manage.py runserver
```

**Terminal 2: Start the Celery Worker**

The Celery worker is responsible for running all the background tasks (training, evaluation, prediction). The `-P solo` flag is used for running on Windows.

```bash
celery -A cidra_ML worker -l info -P solo
```

### 6. Access the Application

Open your web browser and navigate to **`http://127.0.0.1:8000/`**. You can now register a new user and start using Cidra-ML locally!
