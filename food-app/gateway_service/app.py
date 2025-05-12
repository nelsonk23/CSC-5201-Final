from flask import Flask, request, session, redirect, url_for, render_template_string
import requests
app = Flask(__name__)
app.secret_key = 'supersecretkey'
USER_SVC        = 'http://user_service:5001'
ORDER_SVC       = 'http://order_service:5002'
RATING_SVC      = 'http://rating_service:5003'
RECO_SVC        = 'http://recommendation_service:5004'
TRACK_SVC       = 'http://tracking_service:5005'
NOTIFICATION_SVC= 'http://notification_service:5006'
@app.route('/')
def home():
    return render_template_string("""
    <h2>Food Delivery Login</h2>
    <div style="display:flex;justify-content:space-between;width:90%">
      <div>
        <h3>Sign Up</h3>
        <form method="post" action="/signup">
          Username: <input name="username"><br>
          Password: <input name="password" type="password"><br>
          Phone:    <input name="phone"><br>
          <input type="submit" value="Register">
        </form>
      </div>
      <div>
        <h3>Login</h3>
        <form method="post" action="/login">
          Username: <input name="username"><br>
          Password: <input name="password" type="password"><br>
          <input type="submit" value="Login">
        </form>
      </div>
    </div>
    """)
@app.route('/signup', methods=['POST'])
def signup():
    payload = {
        'username': request.form.get('username'),
        'password': request.form.get('password'),
        'phone':    request.form.get('phone')
    }
    resp = requests.post(f"{USER_SVC}/signup", data=payload)
    if resp.status_code == 200:
        session['user_id'] = resp.json()['user_id']
        return redirect(url_for('dashboard'))
    error = resp.json().get('error', resp.text)
    return f"Signup error: {error}", resp.status_code
@app.route('/login', methods=['POST'])
def login():
    payload = {
        'username': request.form.get('username'),
        'password': request.form.get('password')
    }
    resp = requests.post(f"{USER_SVC}/login", data=payload)
    if resp.status_code == 200:
        session['user_id'] = resp.json()['user_id']
        return redirect(url_for('dashboard'))
    error = resp.json().get('error', resp.text)
    return f"Login error: {error}", resp.status_code
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template_string("""
    <h2>Welcome! Choose an option:</h2>
    <ul>
      <li><a href="/order-history">View Order History</a></li>
      <li><a href="/new-order">Place New Order</a></li>
    </ul>
    """)
@app.route('/order-history')
def order_history():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    resp = requests.get(f"{ORDER_SVC}/orders/{uid}")
    orders = resp.json() if resp.ok else []
    html = "<h2>Your Past Orders</h2><ul>"
    for o in orders:
        rid     = o['restaurant_name']
        cuisine = o['cuisine_type']
        time    = o['order_time']
        rr = requests.get(f"{RATING_SVC}/ratings/{rid}").json()
        if rr.get('count', 0):
            rating_info = f"Rated: {rr.get('average_rating')}⭐"
        else:
            rating_info = f"<a href='/rate/{rid}'>⭐ Rate</a>"
        html += (
            f"<li>{rid} ({cuisine}) - {time} | "
            f"{rating_info} | "
            f"<a href='/reorder/{rid}/{cuisine}'>🔁 Re-order</a>"
            "</li>"
        )
    html += "</ul><a href='/dashboard'>Back</a>"
    return html
@app.route('/rate/<restaurant>', methods=['GET','POST'])
def rate(restaurant):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        rating = request.form.get('rating')
        payload = {'restaurant_name': restaurant, 'rating': rating}
        requests.post(f"{RATING_SVC}/ratings", json=payload)
        return redirect(url_for('order_history'))
    return render_template_string("""
    <h2>Rate {{restaurant}}</h2>
    <form method="post">
      Rating (1–5): <input name="rating" type="number" min="1" max="5" required>
      <input type="submit" value="Submit">
    </form>
    """, restaurant=restaurant)
@app.route('/new-order', methods=['GET','POST'])
def new_order():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    if request.method == 'POST':
        payload = {
            'user_id':        uid,
            'cuisine_type':   request.form.get('cuisine_type'),  
                      'restaurant_name':request.form.get('restaurant_name')
        }
        resp = requests.post(f"{ORDER_SVC}/orders/new", json=payload)
        oid = resp.json().get('order_id')
        return redirect(url_for('track', order_id=oid))
    sel_cuisine    = request.args.get('cuisine_type', '')
    sel_restaurant = request.args.get('restaurant_name', '')
    c_resp   = requests.get(f"{ORDER_SVC}/cuisines")
    cuisines = c_resp.json().get('cuisines', [])
    restaurants = []
    if sel_cuisine:
        r_resp      = requests.get(f"{ORDER_SVC}/restaurants/{sel_cuisine}")
        restaurants = r_resp.json().get('restaurants', [])
    rating_text = ''
    if sel_restaurant:
        rr = requests.get(f"{RATING_SVC}/ratings/{sel_restaurant}").json()
        rating_text = f"Rating: {rr.get('average_rating')} ⭐ ({rr.get('count')} reviews)"
    rec = requests.get(f"{RECO_SVC}/recommendations/{uid}").json().get('suggestions', {})
    suggestions_html = ''
    if rec:
        suggestions_html = '<h3>Suggestions Based on Your History:</h3>'
        for cuisine, recs_list in rec.items():
            suggestions_html += f"<strong>{cuisine}</strong><ul>"
            for item in recs_list:
                suggestions_html += (
                    f"<li>{item['restaurant_name']} – "
                    f"{item['average_rating']}⭐ "
                    f"({item['rating_count']})</li>"
                )
            suggestions_html += "</ul>"
    return render_template_string("""
    <form method="get">
      <div style="display:flex;justify-content:space-between;width:90%">
        <div style="width:48%">
          <h2>Place a New Order</h2>
          Cuisine:
          <select name="cuisine_type" onchange="this.form.submit()">
            <option value="">Select</option>
            {% for c in cuisines %}
              <option value="{{c}}" {% if c==sel_cuisine %}selected{% endif %}>{{c}}</option>
            {% endfor %}
          </select><br><br>
          {% if restaurants %}
            Restaurant:
            <select name="restaurant_name" onchange="this.form.submit()">
              <option value="">Select</option>
              {% for r in restaurants %}
                <option value="{{r}}" {% if r==sel_restaurant %}selected{% endif %}>{{r}}</option>
              {% endfor %}
            </select><br><br>
            <p>{{rating_text}}</p>
            <button formaction="" formmethod="post">Place Order</button>
          {% endif %}
         </div>
        <div style="width:48%">{{ suggestions_html|safe }}</div>
      </div>
    </form>
    <a href='/dashboard'>Back</a>
    """,
    cuisines=cuisines,
    restaurants=restaurants,
    sel_cuisine=sel_cuisine,
    sel_restaurant=sel_restaurant,
    rating_text=rating_text,
    suggestions_html=suggestions_html
    )
@app.route('/reorder/<restaurant>/<cuisine>')
def reorder(restaurant, cuisine):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    payload = {
        'user_id':        uid,
        'cuisine_type':   cuisine,
        'restaurant_name':restaurant
    }
    resp = requests.post(f"{ORDER_SVC}/orders/new", json=payload)
    oid = resp.json().get('order_id')
    return redirect(url_for('track', order_id=oid))
@app.route('/track/<order_id>')
def track(order_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    upstream = requests.get(f"{TRACK_SVC}/track/{order_id}/{uid}")
    return upstream.text, upstream.status_code
@app.route('/notify', methods=['POST'])
def notify_user():
    resp = requests.post(
        f"{NOTIFICATION_SVC}/notify",
        json=request.get_json()
    )
    return resp.text, resp.status_code
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
