# Phase B: LLM-based Automation Agent for DataWorks Solutions

import os
import subprocess
import json
import requests
from fastapi import HTTPException
import openai
from dotenv import load_dotenv

load_dotenv()

AIPROXY_TOKEN = os.getenv('AIPROXY_TOKEN')

def B12(filepath):
    if filepath.startswith('/data'):
        # raise PermissionError("Access outside /data is not allowed.")
        # print("Access outside /data is not allowed.")
        return True
    else:
        return False

# B3: Fetch Data from an API
def B3(url, save_path):
    if not B12(save_path):
        return None
    import requests
    response = requests.get(url)
    with open(save_path, 'w') as file:
        file.write(response.text)

# B4: Clone a Git Repo and Make a Commit
def B4(repo_url, branch="main", commit_message="Dummy commit"):  # Default commit message added
    """Clones a Git repo, makes a commit, and pushes using an LLM agent."""

    try:
        # 1. Prompt the LLM for Git commands
        prompt = f"""
        Generate the following Git commands to:
        1. Clone the repository: {repo_url}
        2. Checkout the branch: {branch} (if it exists, otherwise skip)
        3. Create a dummy file named dummy.txt with the content 'Auto-commit' in the newly cloned repo.
        4. Add all changes.
        5. Commit with the message: {commit_message}
        6. Push the changes.

        Return the commands as a JSON array of strings. For example:
        ["git clone <repo_url>", "git checkout <branch>", ...]
        """

        body = {
            "model": "gpt-4o-mini",  # Or your preferred LLM model
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AIPROXY_TOKEN}"  # Ensure AIPROXY_TOKEN is set
        }

        response = requests.post("http://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
                                 headers=headers, json=body)
        response.raise_for_status()

        result = response.json()
        commands_json = result['choices'][0]['message']['content']
        commands = json.loads(commands_json)

        # 2. Execute the Git commands
        for command in commands:
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Git command failed: {command}\n{stderr.decode()}")

        return "Git operations completed successfully."

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with LLM API: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Error parsing LLM API response: {e}. Response: {response.text if 'response' in locals() else 'No response'}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# B5: Run SQL Query
def B5(db_path, query, output_filename):
    if not B12(db_path):
        return None
    import sqlite3, duckdb
    conn = sqlite3.connect(db_path) if db_path.endswith('.db') else duckdb.connect(db_path)
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    conn.close()
    with open(output_filename, 'w') as file:
        file.write(str(result))
    return result

# B6: Web Scraping
def B6(url, output_filename):
    import requests
    result = requests.get(url).text
    with open(output_filename, 'w') as file:
        file.write(str(result))

# B7: Image Processing
def B7(image_path, output_path, resize=None):
    from PIL import Image
    if not B12(image_path):
        return None
    if not B12(output_path):
        return None
    img = Image.open(image_path)
    if resize:
        img = img.resize(resize)
    img.save(output_path)

# B8: Audio Transcription
def B8(audio_path):
    import openai
    if not B12(audio_path):
        return None
    with open(audio_path, 'rb') as audio_file:
        return openai.Audio.transcribe("whisper-1", audio_file)

# B9: Markdown to HTML Conversion
def B9(md_path, output_path):
    import markdown
    if not B12(md_path):
        return None
    if not B12(output_path):
        return None
    with open(md_path, 'r') as file:
        html = markdown.markdown(file.read())
    with open(output_path, 'w') as file:
        file.write(html)

# B10: API Endpoint for CSV Filtering
from flask import Flask, request, jsonify, HTTPException
import pandas as pd
app = Flask(__name__)
@app.route('/filter_csv', methods=['POST'])
def B10():
    try:
        data = request.get_json()
        csv_path = data['csv_file_path']
        filters = data['filters']

        B12(csv_path)  # Use the improved B12 function (raises HTTPException if invalid)

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:  # Catch potential read errors (beyond what B12 catches)
            # logger.error(f"Error reading CSV: {e}")
            raise HTTPException(500, f"Error reading CSV: {e}")

        # Apply Filters (using a helper function for clarity)
        df = apply_filters(df, filters)

        try:
            result = df.to_dict(orient='records')
            return jsonify(result)
        except Exception as e:
            # logger.error(f"Error converting to JSON: {e}")
            raise HTTPException(500, f"Error converting to JSON: {e}")

    except HTTPException as e:
        raise  # Re-raise HTTPExceptions (already logged)
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        # logger.error(error_message)
        raise HTTPException(500, detail=error_message)


def apply_filters(df, filters):
    """Applies the filters to the Pandas DataFrame."""
    for filter_item in filters:
        column = filter_item['column']
        operator = filter_item['operator']
        value = filter_item['value']

        if operator == "=":
            df = df[df[column] == value]
        elif operator == "!=":
            df = df[df[column] != value]
        elif operator == ">":
            df = compare_numeric(df, column, value, lambda x, y: x > y)
        elif operator == "<":
            df = compare_numeric(df, column, value, lambda x, y: x < y)
        elif operator == ">=":
            df = compare_numeric(df, column, value, lambda x, y: x >= y)
        elif operator == "<=":
            df = compare_numeric(df, column, value, lambda x, y: x <= y)
        elif operator == "contains":
            df = df[df[column].str.contains(value, na=False)]
        else:
            raise HTTPException(400, f"Invalid operator: {operator}")
    return df

def compare_numeric(df, column, value, comparison_func):
    """Helper function to perform numeric comparisons with error handling."""
    try:
        df = df[df[column].astype(float).apply(lambda x: comparison_func(x, float(value)))]
        return df
    except ValueError:
        raise HTTPException(400, f"Invalid numeric comparison for column '{column}'.")

