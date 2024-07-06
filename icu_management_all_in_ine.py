import mindsdb_sdk
import sqlite3
import pandas as pd
from flask import Flask, render_template, request

MINDSDB_HOST = 'http://127.0.0.1'
MINDSDB_PORT = 47334  

def connect_to_mindsdb():
    try:
        print("Attempting to connect to MindsDB locally...")
        server = mindsdb_sdk.connect(f"{MINDSDB_HOST}:{MINDSDB_PORT}")
        print("Connected successfully to MindsDB!")
        return server
    except Exception as error:
        print(f"Failed to connect to MindsDB. Error: {error}")
        return None

def load_csv_to_sqlite(csv_file_path, sqlite_db_path):
    try:
        df = pd.read_csv(csv_file_path)
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        df.to_sql('patients', conn, if_exists='replace', index=False)
        print(f"Data from '{csv_file_path}' loaded successfully into '{sqlite_db_path}' database.")
        return conn, cursor
    except Exception as e:
        print(f"Error loading CSV data to SQLite: {e}")
        return None, None

def predict_diagnosis(model, age, gender, symptom1, symptom2, symptom3):
    try:
        result = model.predict({
            'age': age,
            'gender': gender,
            'symptom1': symptom1,
            'symptom2': symptom2,
            'symptom3': symptom3
        })
        return result['diagnosis'], result.get('diagnosis_explain', 'No explanation provided')
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Unable to predict", "An error occurred during prediction"

def get_user_input():
    age = int(input("Enter patient's age: "))
    gender = input("Enter patient's gender (M/F): ")
    symptom1 = input("Enter first symptom: ")
    symptom2 = input("Enter second symptom: ")
    symptom3 = input("Enter third symptom: ")
    return age, gender, symptom1, symptom2, symptom3

def main():
    conn, cursor = load_csv_to_sqlite('large_icu_patients.csv', 'health_data.db')
    if conn is None or cursor is None:
        print("Failed to load CSV data into SQLite. Exiting.")
        return

    server = connect_to_mindsdb()
    if server is None:
        print("Failed to connect to MindsDB. Exiting.")
        return

    try:
        existing_dbs = server.list_databases()
        if 'health_data' not in [db.name for db in existing_dbs]:
            server.databases.create(
                name='health_data',
                engine='sqlite',
                connection_args={
                    'db_file': 'health_data.db'  
                }
            )
            print("SQLite database added as a data source.")
        else:
            print("SQLite database 'health_data' already exists as a data source.")
    except Exception as e:
        print(f"Error handling SQLite database as a data source: {e}")
        return

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
        if cursor.fetchone() is None:
            print("Error: 'patients' table not found in the database.")
            return

        cursor.execute("SELECT COUNT(*) FROM patients")
        row_count = cursor.fetchone()[0]
        print(f"Number of rows in 'patients' table: {row_count}")
        if row_count == 0:
            print("Warning: 'patients' table is empty.")
            return

        try:
            project = server.get_project('health_diagnosis')
            print("Project 'health_diagnosis' already exists.")
        except Exception:
            print("Creating project...")
            project = server.create_project('health_diagnosis')
            print("Project created successfully.")

        try:
            model = project.models.get('diagnosis_predictor')
            print("Model 'diagnosis_predictor' already exists.")
        except Exception:
            print("Creating and training model...")
            model = project.models.create(
                name='diagnosis_predictor',
                predict='diagnosis',
                using={
                    'integration_name': 'health_data',
                    'query': 'SELECT * FROM patients'
                }
            )
            print("Model creation initiated. Waiting for training to complete...")
            model.train()
            print("Model training complete.")

        global prediction_model
        prediction_model = model

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    age = int(request.form['age'])
    gender = request.form['gender']
    symptom1 = request.form['symptom1']
    symptom2 = request.form['symptom2']
    symptom3 = request.form['symptom3']

    diagnosis, explanation = predict_diagnosis(prediction_model, age, gender, symptom1, symptom2, symptom3)

    if diagnosis == 'critical':
        color = 'red'
    elif diagnosis == 'needs_attention':
        color = 'yellow'
    else:
        color = 'green'

    return render_template('result.html', diagnosis=diagnosis, explanation=explanation, color=color)

if __name__ == '__main__':
    main()
    app.run(debug=True, port=5001)  # Use a different port to avoid conflicts




# import mindsdb_sdk
# import sqlite3
# import pandas as pd
# from flask import Flask, render_template, request

# MINDSDB_HOST = 'http://127.0.0.1'
# MINDSDB_PORT = 47334  


# def connect_to_mindsdb():
#     try:
#         print("Attempting to connect to MindsDB locally...")
#         server = mindsdb_sdk.connect(f"{MINDSDB_HOST}:{MINDSDB_PORT}")
#         print("Connected successfully to MindsDB!")
#         return server
#     except Exception as error:
#         print(f"Failed to connect to MindsDB. Error: {error}")
#         return None

# def load_csv_to_sqlite(csv_file_path, sqlite_db_path):
#     try:
#         # Load the CSV file into a DataFrame
#         df = pd.read_csv(csv_file_path)
#         # Connect to SQLite database
#         conn = sqlite3.connect(sqlite_db_path)
#         cursor = conn.cursor()
#         # Create table and load data into SQLite
#         df.to_sql('patients', conn, if_exists='replace', index=False)
#         print(f"Data from '{csv_file_path}' loaded successfully into '{sqlite_db_path}' database.")
#         return conn, cursor
#     except Exception as e:
#         print(f"Error loading CSV data to SQLite: {e}")
#         return None, None

# def predict_diagnosis(model, age, gender, symptom1, symptom2, symptom3):
#     try:
#         result = model.predict({
#             'age': age,
#             'gender': gender,
#             'symptom1': symptom1,
#             'symptom2': symptom2,
#             'symptom3': symptom3
#         })
#         return result['diagnosis'], result.get('diagnosis_explain', 'No explanation provided')
#     except Exception as e:
#         print(f"Error during prediction: {e}")
#         return "Unable to predict", "An error occurred during prediction"

# def get_user_input():
#     age = int(input("Enter patient's age: "))
#     gender = input("Enter patient's gender (M/F): ")
#     symptom1 = input("Enter first symptom: ")
#     symptom2 = input("Enter second symptom: ")
#     symptom3 = input("Enter third symptom: ")
#     return age, gender, symptom1, symptom2, symptom3

# def main():
#     # Load CSV data into SQLite
#     conn, cursor = load_csv_to_sqlite('large_icu_patients.csv', 'health_data.db')
#     if conn is None or cursor is None:
#         print("Failed to load CSV data into SQLite. Exiting.")
#         return

#     # Connect to MindsDB
#     server = connect_to_mindsdb()
#     if server is None:
#         print("Failed to connect to MindsDB. Exiting.")
#         return

#     try:
#         existing_dbs = server.list_databases()
#         if 'health_data' not in [db.name for db in existing_dbs]:
#             server.databases.create(
#                 name='health_data',
#                 engine='sqlite',
#                 connection_args={
#                     'db_file': 'health_data.db'  
#                 }
#             )
#             print("SQLite database added as a data source.")
#         else:
#             print("SQLite database 'health_data' already exists as a data source.")
#     except Exception as e:
#         print(f"Error handling SQLite database as a data source: {e}")

#     # Check if patients table exists and has data
#     try:
#         cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
#         if cursor.fetchone() is None:
#             print("Error: 'patients' table not found in the database.")
#             return

#         cursor.execute("SELECT COUNT(*) FROM patients")
#         row_count = cursor.fetchone()[0]
#         print(f"Number of rows in 'patients' table: {row_count}")
#         if row_count == 0:
#             print("Warning: 'patients' table is empty.")
#             return

#         try:
#             project = server.get_project('health_diagnosis')
#             print("Project 'health_diagnosis' already exists.")
#         except Exception:
#             print("Creating project...")
#             project = server.create_project('health_diagnosis')
#             print("Project created successfully.")

#         try:
#             model = project.models.get('diagnosis_predictor')
#             print("Model 'diagnosis_predictor' already exists.")
#         except Exception:
#             print("Creating and training model...")
#             model = project.models.create(
#                 name='diagnosis_predictor',
#                 predict='diagnosis',
#                 using={
#                     'integration_name': 'health_data',
#                     'query': 'SELECT * FROM patients'
#                 }
#             )
#             print("Model creation initiated. Waiting for training to complete...")
#             model.train()
#             print("Model training complete.")

#         global prediction_model
#         prediction_model = model

#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         if conn:
#             conn.close()

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/predict', methods=['POST'])
# def predict():
#     age = int(request.form['age'])
#     gender = request.form['gender']
#     symptom1 = request.form['symptom1']
#     symptom2 = request.form['symptom2']
#     symptom3 = request.form['symptom3']

#     diagnosis, explanation = predict_diagnosis(prediction_model, age, gender, symptom1, symptom2, symptom3)

#     if diagnosis == 'critical':
#         color = 'red'
#     elif diagnosis == 'needs_attention':
#         color = 'yellow'
#     else:
#         color = 'green'

#     return render_template('result.html', diagnosis=diagnosis, explanation=explanation, color=color)

# if __name__ == '__main__':
#     main()
#     app.run(debug=True)






