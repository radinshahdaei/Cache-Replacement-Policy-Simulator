from collections import deque
import pandas as pd
import csv
import numpy as np

def read_first_n_rows(csv_file, n, index):
    column_values_read = []
    column_values_write = []
    column_values = []
    
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        for i, row in enumerate(csv_reader):
            if i >= n:
                break
            
            column_values.append(int(row[index]))
            
            if(row[4] == "Read"):
                column_values_read.append(int(row[index]))
            if(row[4] == "Write"):
                column_values_write.append(int(row[index]))
                
    return column_values_write, column_values_read, column_values

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
csv_files = ["A42.csv", "A108.csv", "A129.csv", "A669.csv"]

N = int(input("Input queue size: "))
stridal_distance = int(input("Input stridal distance(in bytes): "))

for csv_file in csv_files:
    print(csv_file)
    
    data_write, data_read, data_total = read_first_n_rows(csv_file, n_rows, 2)
    data_write = np.array(data_write)
    data_read = np.array(data_read)
    data_total = np.array(data_total)

    size_write, size_read, size_total = read_first_n_rows(csv_file, n_rows, 3)
    size_write = np.array(size_write)
    size_read = np.array(size_read)
    size_total = np.array(data_total)

    time_write, time_read, time_total = read_first_n_rows(csv_file, n_rows, 0)
    time_write = np.array(time_write)
    time_read = np.array(time_read)
    time_total = np.array(time_total)
    
    print("Write data:")
    calculate_spacial_locality(data_write, size_write, N, stridal_distance)

    print("Read data:")
    calculate_spacial_locality(data_read, size_read, N, stridal_distance)

    print("Total data:")
    calculate_spacial_locality(data_total, size_total, N, stridal_distance)
    
    print("\n")
    
