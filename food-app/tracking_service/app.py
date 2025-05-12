from flask import Flask, render_template_string
import random
app = Flask(__name__)
NOTIFICATION_URL = '/notify'
@app.route('/track/<order_id>/<user_id>')
def track(order_id, user_id):
    total_time = random.randint(10, 25)
    half = total_time // 2
    return render_template_string("""
    <h2>Tracking Order {{ order_id }}</h2>
    <p>Estimated Time Remaining: <span id="timer">{{ total_time }}</span> minutes</p>
    <div style="display:flex;gap:20px;align-items:center;font-size:20px;">
        <div id="step1">🟢<br>Preparing</div>
        <div>━━━</div>
        <div id="step2">⚪<br>Delivering</div>
        <div>━━━</div>
        <div id="step3">⚪<br>Delivered</div>
    </div>
    <script>
    let time = {{ total_time }};
    const half = {{ half }};
    const orderId = "{{ order_id }}";
    const userId  = "{{ user_id }}";
    const notifyUrl = "{{ notification_url }}";
    const interval = setInterval(() => {
        document.getElementById("timer").textContent = time;
        if (time === half) {
            document.getElementById("step2").innerHTML = '🟢<br>Delivering';
        }
        if (time <= 0) {
            document.getElementById("step3").innerHTML = '🟢<br>Delivered';
            // send delivery notification via gateway
            fetch(notifyUrl, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({order_id: orderId, user_id: userId})
            });
            clearInterval(interval);
        }
        time--;
    }, 60000);
    </script>
    <a href="javascript:history.back()">Back</a>
    """,
    order_id=order_id,
    user_id=user_id,
    total_time=total_time,
    half=half,
    notification_url=NOTIFICATION_URL)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
