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
                
    return column_values_read, column_values_write, column_values

def calculate_temporal_locality(time_stamps, offsets, window_size):
    temporal_locality = 0
    dict = {}


    for i in range(len(time_stamps)):
        
        time_stamp = time_stamps[i]
        offset = offsets[i]

        if offset not in dict.keys():
            dict[offset] = int(time_stamp)
        else:
            if int(time_stamp) - int(dict[offset]) <= window_size:
                temporal_locality += 1
            dict[offset] = time_stamp

    print("Temporal locality: {:.2f}%".format(100 * temporal_locality / len(time_stamps)))

n_rows = int(input("Enter sample size: "))
T = [60000000000, 3600000000000, 43200000000000, 86400000000000]

csv_files = ["A669.csv", "A42.csv", "A129.csv", "A108.csv"]

for csv_file in csv_files:
    print(csv_file)
    time_stamps_read, time_stamps_write, time_stamps_total = read_first_n_rows(csv_file, n_rows, 0)
    data_read, data_wrtie, data_total = read_first_n_rows(csv_file, n_rows, 2)
    size_read, size_write, size_total = read_first_n_rows(csv_file, n_rows, 3)
    
    for time in T:
        print("Time window: {}".format(time / 1000000000))
        print("Read")
        calculate_temporal_locality(time_stamps_read, data_read, time)

        print("Write")
        calculate_temporal_locality(time_stamps_write, data_wrtie, time)

        print("Total")
        calculate_temporal_locality(time_stamps_total, data_total, time)
        print("\n")
    print("\n")

