from flask import Flask, request, jsonify
import pandas as pd
import os
from twilio.rest import Client
app = Flask(__name__)
USERS_CSV = '/data/users.csv'
if os.path.exists(USERS_CSV):
    users_df = pd.read_csv(USERS_CSV)
else:
    users_df = pd.DataFrame(columns=['username', 'password', 'phone', 'user_id'])
TW_SID   = os.environ.get('TWILIO_SID')
TW_TOKEN = os.environ.get('TWILIO_TOKEN')
TW_NUMBER= os.environ.get('TWILIO_NUMBER')
client = Client(TW_SID, TW_TOKEN)
@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json()
    user_id  = data.get('user_id')
    order_id = data.get('order_id')
    if not user_id or not order_id:
        return jsonify({'error': 'Missing user_id or order_id'}), 400
    user = users_df[users_df['user_id'] == user_id]
    if user.empty:
        return jsonify({'error': 'User not found'}), 404
    to_phone = user.iloc[0]['phone']
    msg_body = f"Your order {order_id} has been delivered!"
    try:
        message = client.messages.create(
            body=msg_body,
            from_=TW_NUMBER,
            to=to_phone
        )
        return jsonify({'status': 'sent', 'sid': message.sid}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
