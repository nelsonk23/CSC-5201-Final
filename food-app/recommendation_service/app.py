from flask import Flask, jsonify
import pandas as pd
import os
import requests
from collections import Counter
app = Flask(__name__)
DATA_CSV = '/data/food_order.csv'
df = pd.read_csv(DATA_CSV)
cuisine_map = df.groupby('cuisine_type')['restaurant_name'].unique().to_dict()
ORDER_SVC_URL = os.environ.get('ORDER_SVC_URL', 'http://order_service:5002')
RATING_SVC_URL = os.environ.get('RATING_SVC_URL', 'http://rating_service:5003')
@app.route('/recommendations/<user_id>', methods=['GET'])
def recommendations(user_id):
    try:
        resp = requests.get(f'{ORDER_SVC_URL}/orders/{user_id}')
        resp.raise_for_status()
        user_orders = resp.json()
    except Exception:
        return jsonify({'error': 'Could not fetch order history'}), 502
    if not user_orders:
        return jsonify({'suggestions': {}})
    cuisines = Counter(o['cuisine_type'] for o in user_orders)
    suggestions = {}
    for cuisine in cuisines:
        visited = {o['restaurant_name'] for o in user_orders}
        candidates = [r for r in cuisine_map.get(cuisine, []) if r not in visited][:2]
        suggestions[cuisine] = []
        for rest in candidates:
            try:
                r2 = requests.get(f'{RATING_SVC_URL}/ratings/{rest}')
                j2 = r2.json()
                avg = j2.get('average_rating')
                cnt = j2.get('count')
            except Exception:
                avg, cnt = None, 0
            suggestions[cuisine].append({
                'restaurant_name': rest,
                'average_rating': avg,
                'rating_count': cnt
            })
    return jsonify({'suggestions': suggestions})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
