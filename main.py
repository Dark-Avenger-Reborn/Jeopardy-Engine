from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/',)
def main():
    return render_template('index.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    # Get the JSON data sent from the client
    data = request.get_json()

    # Log or process the received data
    print("Received Data:")
    for team in data:
        print(f"Team: {team['teamName']}")
        print(f"Row Checked: {team['rowChecked']}")
        for ip_state in team['ipStates']:
            print(f"IP: {ip_state['ip']}, Checked: {ip_state['isChecked']}")

    # Respond with a success message
    return jsonify({"status": "success", "message": "Data received successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
