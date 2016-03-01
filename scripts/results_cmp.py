#!/usr/bin/env python2

import os, sys, json, glob, math, time, fnmatch
from functools import *

Default_Search_Path = "../"
Signatures = ["algorithm", "alpha", "beta", "dataset", "mark_predecessors", "undirected", "quick_mode"]

# for colored output
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
def Colored(text, color=WHITE):
	return "\x1b[1;%dm" % (30+color) + str(text) + "\x1b[0m"

def JSONFilter(json_file, keywords):
	with open(json_file) as f:
		data = json.load(f)
		for k, v in keywords.iteritems():
			if data.get(k) != v:
				return False
	return True

def JSONExtractor(json_file, key):
	ret = {}
	with open(json_file) as f:
		data = json.load(f)
		for k in key:
			ret[k] = data.get(k)
	return ret

def GatherAllJSON(search_path):
	matches = []
	for root, dirnames, filenames in os.walk(search_path):
		for filename in fnmatch.filter(filenames, "*.json"):
			matches.append(os.path.join(root, filename))
	return matches

input_file = []
all_files = GatherAllJSON(Default_Search_Path)
if len(sys.argv) >= 2:
	input_file = sys.argv[1:]
else:
	print "Usage: {} <Gunrock JSON file 1> [Gunrock JSON file 2]...".format(sys.argv[0])
	sys.exit(0)

# Gunrock outputs only
input_file = filter(partial(JSONFilter, keywords = {"engine" : "Gunrock"}), input_file)
all_files = filter(partial(JSONFilter, keywords = {"engine" : "Gunrock"}), all_files)
# Extract "signatures" from input files
sig = map(partial(JSONExtractor, key = Signatures), input_file)
# Remove duplicated signatures
sig_dedup = []
[sig_dedup.append(i) for i in sig if not i in sig_dedup]
# Collect all JSONs with each signature
collections = map(lambda s: filter(partial(JSONFilter, keywords = s), all_files), sig_dedup)
# print "collection:\n", str(collections).replace("],", "],\n")
# Extract results for each signature
results = map(lambda c: map(partial(JSONExtractor, key = ["elapsed", "time", "m_teps"]), c), collections)
# print "results:\n", str(results).replace("},", "},\n")
# Sort result by ctime
results = map(lambda r: sorted(r, key=lambda k: time.strptime(k["time"].replace("\n", ""))), results)
# print "results:\n", str(results).replace("},", "},\n")

# Generate outputs
for i in range(0, len(sig_dedup)):
	sig_string = ""
	for k, v in sig_dedup[i].iteritems():
		sig_string += "{}={} ".format(k, Colored(str(v), CYAN))
	print Colored("Parameters:", CYAN) + " {}".format(sig_string)
	last_elapsed = float('inf')
	for r in results[i]:
		res_string = "{}:\t".format(r["time"].replace("\n", ""))
		for k, v in r.iteritems():
			if k == "elapsed":
				if last_elapsed < float(v):
					res_string += "{}={}".format(k, Colored(v, RED))
				else:
					res_string += "{}={}".format(k, Colored(v, BLUE))
				if not math.isinf(last_elapsed):
					res_string += " ({:+2.2f}%)\t".format(100 * (float(v) - last_elapsed) / last_elapsed)
				last_elapsed = float(v)
			elif k != "time":
				res_string += "{}={} ".format(k, v)
		print res_string

