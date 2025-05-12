from flask import Flask, request, jsonify
import pandas as pd
import os
app = Flask(__name__)
RATINGS_CSV = '/data/ratings.csv'
if os.path.exists(RATINGS_CSV):
    ratings_df = pd.read_csv(RATINGS_CSV)
else:
    ratings_df = pd.DataFrame(columns=['restaurant_name', 'rating'])
@app.route('/ratings', methods=['POST'])
def add_rating():
    data = request.get_json()
    restaurant = data.get('restaurant_name')
    rating = data.get('rating')
    if not all([restaurant, rating]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        rating = int(rating)
    except ValueError:
        return jsonify({'error': 'Invalid rating'}), 400
    global ratings_df
    ratings_df.loc[len(ratings_df)] = [restaurant, rating]
    ratings_df.to_csv(RATINGS_CSV, index=False)
    return jsonify({'status': 'success'}), 201
@app.route('/ratings/<restaurant>', methods=['GET'])
def get_ratings(restaurant):
    df = ratings_df[ratings_df['restaurant_name'] == restaurant]
    if df.empty:
        return jsonify({'average_rating': None, 'count': 0})
    avg = df['rating'].mean().round(2)
    count = int(df['rating'].count())
    return jsonify({'average_rating': avg, 'count': count})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
