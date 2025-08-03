import json
import matplotlib.pyplot as plt

# Function to load metrics from JSON file
def load_metrics(filename):
    with open(filename, "r") as f:
        metrics = json.load(f)
    return metrics

# Function to plot individual comparisons for each metric
def plot_individual_comparisons(protocol_1_metrics, protocol_2_metrics):
    metrics = [
        ('Packets Sent', protocol_1_metrics['packets_sent'], protocol_2_metrics['packets_sent']),
        ('Errors Detected', protocol_1_metrics['errors_detected'], protocol_2_metrics['errors_detected']),
        ('Error Rate (%)', protocol_1_metrics['error_rate'], protocol_2_metrics['error_rate']),
        ('Avg Latency (sec)', protocol_1_metrics['avg_latency'], protocol_2_metrics['avg_latency']),
        ('Power Consumption (mW)', protocol_1_metrics['power_mw'], protocol_2_metrics['power_mw'])
    ]
    
    # Iterate through each metric and generate a comparison graph
    for metric_name, protocol_1_value, protocol_2_value in metrics:
        # Plot
        plt.figure(figsize=(6, 4))
        x = ['spacefibre', 'spacewire']
        y = [protocol_1_value, protocol_2_value]
        
        plt.bar(x, y, color=['blue', 'green'])
        plt.title(f'{metric_name} Comparison')
        plt.ylabel(metric_name)
        plt.xlabel('Protocols')
        plt.tight_layout()
        plt.savefig(f"{metric_name.replace(' ', '_').lower()}_comparison.png")
        # Show the graph
        plt.show()

# Load the metrics for both protocols
protocol_1_metrics = load_metrics("spacefibre_metrics.json")  # Example: SpaceFibre
protocol_2_metrics = load_metrics("spacewire_metrics.json")  # Example: SpaceWire

# Plot individual comparisons
plot_individual_comparisons(protocol_1_metrics, protocol_2_metrics)
