from flask import Flask, request, jsonify, render_template
import ansible_automator
import threading

app = Flask(__name__)

@app.route('/',)
def main():
    return render_template('index.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    # Get the JSON data sent from the client
    data = request.get_json()

    string_of_ips = ""

    # Log or process the received data
    print("Received Data:")
    for team in data:
        for ip_state in team['ipStates']:
            if ip_state['isChecked']:
                print(ip_state['ip'])
                if (":" in ip_state['ip']):
                    finalIP = ip_state['ip'].split(":")[0]
                else:
                    finalIP = ip_state['ip']
                string_of_ips += finalIP + ","

    string_of_ips = string_of_ips[:-1]
    print(string_of_ips)


    inventory_path = "./ansible_recources/real.ini"
    playbook_path = "/path/to/playbook.yml"
    
    #threading.Thread(target=ansible_automator.run_playbook, args=(inventory_path, playbook_path, string_of_ips))

    # Respond with a success message
    return jsonify({"status": "success", "message": "Data received successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
