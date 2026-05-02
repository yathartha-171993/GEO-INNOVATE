"""
GEO-INNOVATE: Local Innovation Map
Copyright (C) 2026 Yathartha Mishra

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""
import os
import pandas as pd
from flask import Flask, render_template, jsonify, request, redirect, session, url_for

app = Flask(__name__)

# Essential for using sessions and flashes
app.secret_key = "arque_innovate_secure_key" 

# File paths
CSV_FILE = 'innovations.csv'
PENDING_FILE = 'submissions.csv'
UPLOAD_FOLDER = 'static/uploads/'

# Ensure required directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Robust initialization to prevent EmptyDataError
cols = ['Name', 'Description', 'Lat', 'Lng', 'Category', 'Roadmap', 'ImageURL']
for f in [CSV_FILE, PENDING_FILE]:
    # If file doesn't exist OR is empty, write headers
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        pd.DataFrame(columns=cols).to_csv(f, index=False)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/markers')
def get_markers():
    try:
        df = pd.read_csv(CSV_FILE)
        return jsonify(df.fillna('').to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- USER SUBMISSION ---

@app.route('/submit', methods=['POST'])
def submit_product():
    file = request.files.get('image')
    if file and file.filename != '':
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        new_entry = {
            'Name': request.form.get('name'),
            'Description': request.form.get('desc'),
            'Lat': request.form.get('lat'),
            'Lng': request.form.get('lng'),
            'Category': request.form.get('category', 'default'),
            'Roadmap': request.form.get('roadmap', 'Scaling strategy pending review.'),
            'ImageURL': '/' + filepath.replace('\\', '/') # Ensure web-friendly slashes
        }
        
        df_pending = pd.read_csv(PENDING_FILE)
        df_pending = pd.concat([df_pending, pd.DataFrame([new_entry])], ignore_index=True)
        df_pending.to_csv(PENDING_FILE, index=False)
        
        return redirect(url_for('index'))
    return "Image upload failed", 400

# --- ADMIN DASHBOARD ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('admin_dash'))
    return render_template('login.html')

@app.route('/admin')
def admin_dash():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    df_pending = pd.read_csv(PENDING_FILE)
    items = df_pending.to_dict(orient='records')
    return render_template('admin.html', items=items)

@app.route('/approve/<name>')
def approve_item(name):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    df_pending = pd.read_csv(PENDING_FILE)
    approved_row = df_pending[df_pending['Name'] == name]
    
    if not approved_row.empty:
        df_main = pd.read_csv(CSV_FILE)
        df_main = pd.concat([df_main, approved_row], ignore_index=True)
        df_main.to_csv(CSV_FILE, index=False)
        
        df_pending = df_pending[df_pending['Name'] != name]
        df_pending.to_csv(PENDING_FILE, index=False)
        
    return redirect(url_for('admin_dash'))

@app.route('/remove/<name>')
def remove_item(name):
    """Deletes a submission from both pending and live files."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # 1. Check and remove from PENDING_FILE (submissions.csv)
    df_pending = pd.read_csv(PENDING_FILE)
    if not df_pending[df_pending['Name'] == name].empty:
        df_pending = df_pending[df_pending['Name'] != name]
        df_pending.to_csv(PENDING_FILE, index=False)

    # 2. Check and remove from CSV_FILE (innovations.csv)
    # This is what enables the "Delete" button on your admin live list to work
    df_main = pd.read_csv(CSV_FILE)
    if not df_main[df_main['Name'] == name].empty:
        df_main = df_main[df_main['Name'] != name]
        df_main.to_csv(CSV_FILE, index=False)
    
    return redirect(url_for('admin_dash'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
