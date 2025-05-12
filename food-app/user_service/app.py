from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import os
import random
app = Flask(__name__)
app.secret_key = 'supersecretkey'
USERS_CSV = '/data/users.csv'
def load_users():
    if os.path.exists(USERS_CSV):
        return pd.read_csv(USERS_CSV)
    return pd.DataFrame(columns=['username', 'password', 'phone', 'user_id'])
users_df = load_users()
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    phone = request.form.get('phone')
    if not phone.startswith('+'):
        phone = '+1' + phone
    if not all([username, password, phone]):
        return jsonify({'error': 'Missing fields'}), 400
    if username in users_df['username'].values:
        return jsonify({'error': 'Username already exists'}), 409
    user_id = f"U{random.randint(1000, 9999)}"
    users_df.loc[len(users_df)] = [username, password, phone, user_id]
    users_df.to_csv(USERS_CSV, index=False)
    return jsonify({'user_id': user_id}), 200
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not all([username, password]):
        return jsonify({'error': 'Missing fields'}), 400
    user = users_df[
        (users_df['username'] == username) &
        (users_df['password'] == password)
    ]
    if user.empty:
        return jsonify({'error': 'Invalid login'}), 401
    return jsonify({'user_id': user.iloc[0]['user_id']}), 200
@app.route('/signup', methods=['GET'])
def signup_form():
    return render_template_string("""
    <h2>Sign Up</h2>
    <form method="post">
      Username: <input name="username"><br>
      Password: <input name="password" type="password"><br>
      Phone: <input name="phone"><br>
      <input type="submit" value="Register">
    </form>
    """)
@app.route('/login', methods=['GET'])
def login_form():
    return render_template_string("""
    <h2>Login</h2>
    <form method="post">
      Username: <input name="username"><br>
      Password: <input name="password" type="password"><br>
      <input type="submit" value="Login">
    </form>
    """)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
