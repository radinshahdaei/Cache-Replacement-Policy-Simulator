from collections import deque
import pandas as pd
import csv
import numpy as np

def read_first_n_rows(csv_file, n, index):
    column_values = []
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        for i, row in enumerate(csv_reader):
            if i >= n:
                break
            column_values.append(int(row[index]))
    return column_values

n_rows = int(input()) # Only take a sample from the file to save time.
csv_file = "A669.csv"
time_stamps = read_first_n_rows(csv_file, n_rows, 0)
time_stamps = np.array(time_stamps)
data = read_first_n_rows(csv_file, n_rows, 2)
data = np.array(data)
size = read_first_n_rows(csv_file, n_rows, 3)
size = np.array(size)

data = pd.DataFrame({
    'TimeStamp': time_stamps,
    'Offset': data,
    'Size': size
})

# Parameters
T = int(input("Enter time window in secods:"))
T = T * 1000000000

active_requests = deque()
temporal_locality_count = 0
total_requests = 0

data = data.sort_values(by='TimeStamp')

def has_overlap(request1, request2):
    start1, size1 = request1
    start2, size2 = request2
    return not (start1 + size1 <= start2 or start2 + size2 <= start1)

for _, row in data.iterrows():
    timestamp, offset, size = row['TimeStamp'], row['Offset'], row['Size']
    current_request = (offset, size)
    total_requests += 1

    while active_requests and active_requests[0][0] + T < timestamp:
        active_requests.popleft()

    for request in active_requests:
        if has_overlap(request[1], current_request):
            temporal_locality_count += 1
            break

    active_requests.append((timestamp, current_request))

temporal_locality_ratio = temporal_locality_count / total_requests

print(f"Total Requests: {total_requests}")
print(f"Temporal Locality Count: {temporal_locality_count}")
print(f"Temporal Locality Ratio: {temporal_locality_ratio:.4f}")
