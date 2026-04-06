from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

PORT = 3000

attacks = [
    {
        "id": "ATK001",
        "timestamp": int(datetime.now().timestamp() * 1000) - 300000,
        "endpoint": "/api/users",
        "method": "GET",
        "requestsPerSecond": 5000,
        "sourceIPs": 342,
        "severity": "critical",
        "status": "mitigated"
    },
    {
        "id": "ATK002",
        "timestamp": int(datetime.now().timestamp() * 1000) - 60000,
        "endpoint": "/api/auth/login",
        "method": "POST",
        "requestsPerSecond": 2300,
        "sourceIPs": 156,
        "severity": "high",
        "status": "active"
    }
]

@app.route('/api/attacks', methods=['GET'])
def get_attacks():
    """Returns all detected attacks"""
    return jsonify(attacks)

@app.route('/api/attacks/<id>', methods=['GET'])
def get_attack(id):
    """Returns a specific attack by ID"""
    attack = next((a for a in attacks if a["id"] == id), None)
    if not attack:
        return jsonify({"error": "Attack not found"}), 404
    return jsonify(attack)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Returns attack statistics"""
    active_count = len([a for a in attacks if a["status"] == "active"])
    avg_reqs_per_sec = round(sum(a["requestsPerSecond"] for a in attacks) / len(attacks)) if attacks else 0
    critical_count = len([a for a in attacks if a["severity"] == "critical"])
    high_count = len([a for a in attacks if a["severity"] == "high"])
    
    return jsonify({
        "totalAttacks": len(attacks),
        "activeAttacks": active_count,
        "averageRequestsPerSecond": avg_reqs_per_sec,
        "criticalCount": critical_count,
        "highCount": high_count
    })

@app.route('/api/attacks', methods=['POST'])
def create_attack():
    """Add a new attack (for testing/simulation)"""
    data = request.get_json()
    
    new_attack = {
        "id": f"ATK{str(len(attacks) + 1).zfill(3)}",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "endpoint": data.get("endpoint", "/api/unknown"),
        "method": data.get("method", "GET"),
        "requestsPerSecond": data.get("requestsPerSecond", 0),
        "sourceIPs": data.get("sourceIPs", 0),
        "severity": data.get("severity", "low"),
        "status": "detected"
    }
    
    attacks.append(new_attack)
    return jsonify(new_attack), 201

@app.route('/api/attacks/<id>', methods=['PUT'])
def update_attack(id):
    """Update attack status (e.g., mark as mitigated)"""
    attack = next((a for a in attacks if a["id"] == id), None)
    if not attack:
        return jsonify({"error": "Attack not found"}), 404
    
    data = request.get_json()
    if "status" in data:
        attack["status"] = data["status"]
    
    return jsonify(attack)

@app.route('/api/attacks/<id>', methods=['DELETE'])
def delete_attack(id):
    """Remove an attack record"""
    global attacks
    attacks = [a for a in attacks if a["id"] != id]
    return jsonify({"message": "Attack deleted"})

if __name__ == '__main__':
    print(f"🛡️  DDoS Detection Server running on http://localhost:{PORT}")
    app.run(debug=True, port=PORT, host='localhost')
