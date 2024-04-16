# import numpy as np

def prune(data_set, outlier_ratio=0.5):
    """Function that takes in a data set and returns the average, excluding the amount
    of outliers specified.
    """
    outliers = []
    pruned_data = [i for i in data_set]
    for _ in range(int(outlier_ratio*len(data_set))):
        if abs(max(pruned_data)-sum(pruned_data)/len(pruned_data)) > abs(min(pruned_data)-sum(pruned_data)/len(pruned_data)):
            outliers += [max(pruned_data)]
            pruned_data.remove(max(pruned_data))
        else:
            outliers += [min(pruned_data)]
            pruned_data.remove(min(pruned_data))
    return sum(pruned_data)/len(pruned_data)

def dot_product(arr1, arr2):
    return sum([arr1[i]*arr2[i] for i in range(len(arr1))])