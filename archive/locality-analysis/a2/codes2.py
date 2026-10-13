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

def calculate_spacial_locality(addresses, sizes, N, stridal_distance):
    sequential_count = 0
    overlapping_count = 0
    stridal_count = 0
    random_count = 0
    queue = []

    for i in range(len(addresses)):
        address = addresses[i]
        size = sizes[i]

        found_category = False
        # Check sequential
        for req_address, req_size in queue:
            if address == req_address + req_size:
                sequential_count += 1
                found_category = True
                break
        # Check overlapping
        if found_category == False:
            for req_address, req_size in queue:
                if (address >= req_address and address <= req_address + req_size) or \
                     (address + size >= req_address and address + size <= req_address + req_size):
                    overlapping_count += 1
                    found_category = True
                    break
        # Checck stridal
        if found_category == False:
            for req_address, req_size in queue:
                if abs(max(address, req_address) - min(address + size, req_address + req_size)) <= stridal_distance:
                    stridal_count += 1
                    found_category = True
                    break

        if not found_category:
            random_count += 1

        # Update the queue
        queue.append((address, size))
        if len(queue) > N:
            queue.pop(0)

    total_requests = len(addresses)
    percent_sequential = (sequential_count / total_requests) * 100
    percent_overlapping = (overlapping_count / total_requests) * 100
    percent_stridal = (stridal_count / total_requests) * 100
    percent_random = (random_count / total_requests) * 100

    print("Sequential: {:.2f}%".format(percent_sequential))
    print("Overlapping: {:.2f}%".format(percent_overlapping))
    print("Stridal: {:.2f}%".format(percent_stridal))
    print("Random: {:.2f}%".format(percent_random))

n_rows = int(input("Input sample size: ")) # Only take a sample from the file to save time.
csv_file = "A42.csv"

data = read_first_n_rows(csv_file, n_rows, 2)
data = np.array(data)
size = read_first_n_rows(csv_file, n_rows, 3)
size = np.array(size)

N = int(input("Input queue size: "))
stridal_distance = int(input("Input stridal distance(in bytes): "))
calculate_spacial_locality(data, size, N, stridal_distance)
