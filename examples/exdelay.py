import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the parent directory to the path so we can import pysydy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pysydy

def delay_example():
    """
    Demonstrates the use of different delay types in PySyDy.
    """
    print("\n=== Delay Example ===")
    
    # Create delay objects
    material_delay = pysydy.MaterialDelay(name="Material Delay", delay_time=5.0, initial_value=0.0, order=4)
    info_delay = pysydy.InformationDelay(name="Information Delay", delay_time=5.0, initial_value=0.0, order=3)
    fixed_delay = pysydy.FixedDelay(name="Fixed Delay", delay_time=5.0, initial_value=0.0, timestep=1.0)
    
    # Simulate a step input
    time_points = np.arange(0, 20, 1.0)
    material_outputs = []
    info_outputs = []
    fixed_outputs = []
    
    for t in time_points:
        # Step input at t=5
        input_value = 0.0 if t < 5 else 10.0
        
        # Update delays
        material_out = material_delay.update(input_value, 1.0)
        info_out = info_delay.update(input_value, 1.0)
        fixed_out = fixed_delay.update(input_value, 1.0)
        
        # Record outputs
        material_outputs.append(material_out)
        info_outputs.append(info_out)
        fixed_outputs.append(fixed_out)
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(time_points, [0.0 if t < 5 else 10.0 for t in time_points], 'k--', label='Input')
    plt.plot(time_points, material_outputs, label='Material Delay')
    plt.plot(time_points, info_outputs, label='Information Delay')
    plt.plot(time_points, fixed_outputs, label='Fixed Delay')
    plt.title('Comparison of Delay Types')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    #plt.savefig('delay_comparison.png')
    plt.show()

if __name__ == "__main__":
    delay_example()