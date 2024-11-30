import json

def simulate_particle_behavior():
    # Example simulation of particle metadata for demonstration purposes
    particle_metadata = {
        "ParticleID": "E123",
        "Type": "Electron",
        "QuantumState": {
            "Position": [1.2e-35, -2.3e-35, 3.1e-35],
            "Momentum": [1.6e-27, -2.8e-27, 3.5e-27],
            "Spin": "Up"
        },
        "InteractionRules": {
            "Charge": -1,
            "Mass": 9.11e-31
        }
    }

    # Print the particle's metadata as a JSON object
    print("Simulated Particle Metadata:")
    print(json.dumps(particle_metadata, indent=2))

if __name__ == "__main__":
    simulate_particle_behavior()
