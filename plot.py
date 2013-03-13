import numpy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
import csv
import sys

response_time = []
percentages = []

data = csv.reader(open(sys.argv[1],'rU'))
for row in data:
	response_time.append(float(row[0]))
	percentages.append(100 * float(row[1]))

pyplot.figure()
pyplot.xlabel("Keystroke response time (seconds)")
pyplot.ylabel("Percentage")
pyplot.plot(response_time, percentages, 'b.', response_time, percentages, 'k')
pyplot.savefig(sys.argv[1] + ".png")