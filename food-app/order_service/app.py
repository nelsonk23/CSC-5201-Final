from flask import Flask, request, jsonify
import pandas as pd
import os
import random
from datetime import datetime
app = Flask(__name__)
ORDERS_CSV = '/data/orders.csv'
DATA_CSV   = '/data/food_order.csv'
if os.path.exists(ORDERS_CSV):
    orders_df = pd.read_csv(ORDERS_CSV)
else:
    orders_df = pd.DataFrame(columns=[
        'order_id', 'user_id', 'restaurant_name', 'cuisine_type', 'order_time'
    ])
master_df   = pd.read_csv(DATA_CSV)
cuisine_map = master_df.groupby('cuisine_type')['restaurant_name'] \
                       .unique().to_dict()
@app.route('/cuisines', methods=['GET'])
def get_cuisines():
    """Return list of all cuisine types."""
    return jsonify({'cuisines': list(cuisine_map.keys())})
@app.route('/restaurants/<cuisine>', methods=['GET'])
def get_restaurants(cuisine):
    """Return all restaurants for a given cuisine."""
    rests = cuisine_map.get(cuisine, [])
    return jsonify({'restaurants': list(rests)})
@app.route('/orders/new', methods=['POST'])
def new_order():
    data = request.get_json()
    user_id    = data.get('user_id')
    restaurant = data.get('restaurant_name')
    cuisine    = data.get('cuisine_type')
    if not all([user_id, restaurant, cuisine]):
        return jsonify({'error': 'Missing fields'}), 400
    order_id  = f"ORD{random.randint(100000, 999999)}"
    order_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    global orders_df
    orders_df.loc[len(orders_df)] = [
        order_id, user_id, restaurant, cuisine, order_time
    ]
    orders_df.to_csv(ORDERS_CSV, index=False)
    return jsonify({'order_id': order_id, 'order_time': order_time}), 201
@app.route('/orders/<user_id>', methods=['GET'])
def get_orders(user_id):
    user_orders = orders_df[orders_df['user_id'] == user_id]
    return jsonify(user_orders.to_dict(orient='records'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
