def prune(data_set, outlier_ratio=0.5):
    """Function that takes in a data set and returns the average, excluding the amount
    of outliers specified.
    """
    outliers = []
    for _ in range(int(outlier_ratio*len(data_set)/2)):
        outliers += [max(data_set), min(data_set)]
        pruned_avg = (sum(data_set)-sum(outliers))/(len(data_set)-len(outliers))
    return pruned_avg

def dot_product(arr1, arr2):
    return sum([arr1[i]*arr2[i] for i in range(len(arr1))])