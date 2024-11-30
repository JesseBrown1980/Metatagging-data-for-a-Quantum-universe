import numpy as np
import json

class QuantumParticle:
    def __init__(self, particle_id, position, momentum, spin, charge, mass):
        self.particle_id = particle_id
        self.position = np.array(position)  # Position in the 3D vector space
        self.momentum = np.array(momentum)  # Momentum vector
        self.spin = spin
        self.charge = charge
        self.mass = mass

    def to_dict(self):
        return {
            "ParticleID": self.particle_id,
            "QuantumState": {
                "Position": self.position.tolist(),
                "Momentum": self.momentum.tolist(),
                "Spin": self.spin
            },
            "InteractionRules": {
                "Charge": self.charge,
                "Mass": self.mass
            }
        }

    def update_position(self, displacement):
        """Updates the position of the particle."""
        self.position += np.array(displacement)
        print(f"{self.particle_id} moved to new position: {self.position}")

# Define function to create an entangled state between two particles
def create_entanglement(p1, p2):
    shared_state = {
        "EntangledWith": [p1.particle_id, p2.particle_id],
        "SharedState": {
            "Spin": "Opposite",
            "PhaseCorrelation": 1.0
        }
    }
    return shared_state

# Initialize two particles
particle1 = QuantumParticle("P1", [1.2e-35, -2.3e-35, 3.1e-35], [1.6e-27, -2.8e-27, 3.5e-27], "Up", -1, 9.11e-31)
particle2 = QuantumParticle("P2", [-1.2e-35, 2.3e-35, -3.1e-35], [-1.6e-27, 2.8e-27, -3.5e-27], "Down", -1, 9.11e-31)

# Create an entangled state
entanglement = create_entanglement(particle1, particle2)

# Print out the metadata for both particles and their entanglement
print("Particle 1 Metadata:")
print(json.dumps(particle1.to_dict(), indent=2))

print("\nParticle 2 Metadata:")
print(json.dumps(particle2.to_dict(), indent=2))

print("\nEntanglement Metadata:")
print(json.dumps(entanglement, indent=2))

# Example of expanding the vector space by moving particle1
particle1.update_position([0.5e-35, 0.5e-35, 0.0])

# Add particle metadata to a JSON file to illustrate metatagging storage
with open('particle_metadata.json', 'w') as f:
    json.dump({
        "Particle1": particle1.to_dict(),
        "Particle2": particle2.to_dict(),
        "Entanglement": entanglement
    }, f, indent=2)

print("\nMetadata saved to particle_metadata.json")
