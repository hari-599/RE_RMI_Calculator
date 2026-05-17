# 🌍 Renewable Energy - Regional Maturity Index (RE-RMI)

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-black?style=for-the-badge&logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Deployment-Render-purple?style=for-the-badge&logo=render&logoColor=white)
![Status](https://img.shields.io/badge/Status-Client_Review-orange?style=for-the-badge)

**[View Live Application](https://re-rmi-calculator.onrender.com/)**

A web-based decision support system designed to calculate the **Regional Maturity Index (RMI)** for Renewable Energy projects. This tool digitizes a proprietary mathematical model provided by the client, allowing stakeholders to assess the readiness of different regions for energy infrastructure investments.

> **Note:** The underlying mathematical index and scoring logic were developed by the client. My role was to engineer the web architecture, data processing layer, and user interface to operationalize this model.

## 🚀 Key Features
* **Digitized Assessment Model:** Transformed complex theoretical frameworks into a functional Python-based calculation engine.
* **Weighted Scoring System:** Implements dynamic variable processing (e.g., Policy Readiness, Grid Infrastructure, Economic Indicators) to generate a composite Maturity Score.
* **Interactive Dashboard:** Built a clean, responsive UI for researchers to input regional data and visualize maturity gradients.
* **Cloud-Native:** Deployed on **Render** to ensure global accessibility for the client's research team.

## 🛠️ Tech Stack
* **Backend Logic:** Python, Flask
* **Data Processing:** Pandas (for weighted index calculations)
* **Frontend:** HTML5, CSS3, Jinja2
* **Deployment:** Docker, Render

## Project Structure

```text
re-rmi/
|-- app.py
|-- requirements.txt
|-- scripts/
|   |-- create_db.py
|   `-- extract_recommendations_to_py.py
|-- src/
|   `-- re_rmi/
|       |-- __init__.py
|       |-- routes.py
|       |-- models.py
|       |-- forms.py
|       |-- extensions.py
|       |-- process_excel.py
|       |-- contributions.py
|       |-- recommendations_data.py
|       |-- static/
|       `-- templates/
`-- instance/
```

## Running Locally

```powershell
.\env\Scripts\activate
pip install -r requirements.txt
python app.py
```

The root `app.py` file is intentionally kept as a lightweight entry point for local development and deployment platforms. The Flask application package now lives in `src/re_rmi`.
