import pandas as pd
import matplotlib.pyplot as plt

# Define the data (updated structure)
data = {
    "File": ["A42.csv", "A108.csv", "A129.csv", "A669.csv"],
    "0": [0, 0, 0, 0],
    "1": [1127, 17841, 33570, 513],
    "2": [246, 15282, 31859, 131],
    "4": [651, 15506, 53711, 239],
    "8": [79261, 20316, 48780, 8262],
    "16": [138003, 105602, 180865, 14346],
    "32": [70701, 214345, 559419, 21776],
    "64": [60607, 499300, 714568, 29490],
    "128": [104420, 501887, 656727, 160389],
    "256": [160848, 567200, 533946, 188223],
    "512": [80518, 261887, 307094, 129981],
    "1.0K": [66372, 227522, 258043, 479616],
    "2.0K": [68399, 336993, 282024, 3690084],
    "4.0K": [54804, 240031, 461484, 13824218],
    "8.0K": [45991, 347200, 485149, 5948409],
    "16.0K": [46548, 306742, 417581, 1371647],
    "32.0K": [181995, 494339, 2760648, 196362],
    "64.0K": [1013753, 447099, 752516, 315843],
    "128.0K": [2746811, 658565, 939909, 284963],
    "256.0K": [12529, 1612585, 1632888, 401310],
    "512.0K": [0, 9176992, 1839626, 0],
    ">512K": [0, 2479554, 1762889, 0]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Set 'File' as the index
df.set_index('File', inplace=True)

# Transpose the DataFrame for plotting
df = df.transpose()

# Plot the data
plt.figure(figsize=(14, 8))
for column in df.columns:
    if column not in ['avg', 'min', 'max']:  # Exclude avg, min, max columns
        plt.plot(df.index, df[column], marker='o', label=column)

plt.title('Data Plot')
plt.xlabel('Buckets')
plt.ylabel('Values')
plt.xticks(rotation=90)
plt.legend(title='Files')
plt.grid(True)
plt.tight_layout()

plt.savefig('plot.png')  # Save the plot as PNG file
plt.show()  # Show the plot
