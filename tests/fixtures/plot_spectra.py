import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
# Add project root to sys.path to allow absolute imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.append(root_path)

from src.readers.csv_reader import CSVReader

def plot_nmr_spectra(csv_path: str):
    """
    Reads an NMR consolidated CSV and plots the spectra using matplotlib.
    Follows the standard NMR convention: PPM maximum on the left, 0 or minimum on the right.
    """
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Reading data from {csv_path}...")
    try:
        reader: CSVReader = CSVReader()
        df: pd.DataFrame = reader.read(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if 'PPM' not in df.columns:
        print("Error: 'PPM' column not found in the CSV.")
        return

    # Extract PPM scale
    ppm: pd.Series = df['PPM']
    
    # All other columns are experiments
    experiments: list[str] = [col for col in df.columns if col != 'PPM']

    if not experiments:
        print("No experiment columns found in the CSV.")
        return

    plt.figure(figsize=(12, 6))

    # Plot each experiment with a distinct color
    for exp in experiments:
        plt.plot(ppm, df[exp], label=exp, linewidth=1)

    # Set labels and title
    plt.xlabel('Chemical Shift (PPM)')
    plt.ylabel('Intensity')
    plt.title('NMR Spectra Visualization')
    
    # Legend
    # plt.legend(loc='upper right', fontsize='small', ncol=2)

    # Standard NMR Convention: Max PPM on the left, Min PPM on the right
    plt.xlim(ppm.max(), ppm.min())

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Save the plot distinctively so it doesn't overwrite
    basename: str = os.path.splitext(os.path.basename(csv_path))[0]
    output_image: str = os.path.join(os.path.dirname(csv_path), f"spectra_plot_{basename}.png")
    plt.savefig(output_image, dpi=300)
    print(f"Plot saved successfully at: {output_image}")
    # Show plot (if environment supports it)
    # plt.show()

if __name__ == "__main__":
    # Path to the consolidated CSV relative to the project root
    # Since this script is inside tests/fixtures/, we need to go up two directories (.., ..)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    files_to_plot = [
        "LNBio03_Bruker_600MHz_Urina_size180.csv",
        "LNBio04_Agilent_500MHz_Soro_size137.csv"
    ]
    
    for fname in files_to_plot:
        csv_file = os.path.join(base_dir, "outputs", "csv_tables", fname)
        plot_nmr_spectra(csv_file)
