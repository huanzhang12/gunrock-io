#!/usr/bin/env python2

import os, sys, json, glob, math, time, fnmatch
from functools import *

# We will compare to input file to all JSON files with the same signature inside the search path
Default_Search_Path = "../gunrock-output/"
Signatures = ["algorithm", "alpha", "beta", "dataset", "idempotent", "source_vertex", "mark_predecessors", "undirected", "quick_mode"]
# All JSON files will be loaded in this buffer
JSON_buffer = {}

# for colored output
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
#following from Python cookbook, #475186
def has_colors(stream):
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False
Term_Has_Colors = has_colors(sys.stdout)
def Colored(text, color=WHITE):
	if  Term_Has_Colors:
		return "\x1b[1;%dm" % (30+color) + str(text) + "\x1b[0m"
	else:
		return str(text)

# Filter JSON by key/value
def JSONFilter(json_file, keywords):
	for k, v in keywords.iteritems():
		if JSON_buffer[json_file].get(k) != v:
			return False
	return True

# Extract key/value from JSON
def JSONExtractor(json_file, key):
	ret = {}
	for k in key:
		ret[k] = JSON_buffer[json_file].get(k)
	return ret

# Find the paths of all JSON files in search path
def GatherAllJSON(search_path):
	matches = []
	for root, dirnames, filenames in os.walk(search_path):
		for filename in fnmatch.filter(filenames, "*.json"):
			matches.append(os.path.abspath(os.path.join(root, filename)))
	print "Found {} JSON files in search path {}".format(len(matches), search_path)
	return matches

# Parse All JSON files and load them into a dictionary, filename as the key
def LoadAllJSON(filelist):
	for j in filelist:
		with open(j) as f:
			JSON_buffer[j] = json.load(f)
	
# Generate outputs
def PrintResults(sig_dedup, results):
	for i in range(0, len(sig_dedup)):
		# only one result given this signature, do not print
		if len(results[i]) < 2:
			continue
		sig_string = ""
		for k, v in sig_dedup[i].iteritems():
			sig_string += "{}={} ".format(k, Colored(str(v), CYAN))
		print Colored("Parameters:", CYAN) + " {}".format(sig_string)
		last_elapsed = float('inf')
		percent = 0.0
		for r in results[i]:
			res_string = "{}:\t".format(r["time"].replace("\n", ""))
			for k, v in r.iteritems():
				if k == "elapsed":
					if not math.isinf(last_elapsed):
						percent = 100 * (float(v) - last_elapsed) / last_elapsed
					if percent > 2.0:
						res_string += "{}={}".format(k, Colored(v, RED))
						res_string += " ({:+2.2f}%)\t".format(percent)
					elif percent < -2.0:
						res_string += "{}={}".format(k, Colored(v, GREEN))
						res_string += " ({:+2.2f}%)\t".format(percent)
					else:
						res_string += "{}={}".format(k, Colored(v, BLUE))
					last_elapsed = float(v)
				elif k != "time":
					res_string += "{}={} ".format(k, v)
			print res_string

# Preparing JSON files
input_file = []
all_files = GatherAllJSON(Default_Search_Path)
if len(sys.argv) >= 2:
	input_file = set(map(os.path.abspath, sys.argv[1:]))
else:
	print "Not giving an input file list, compare all files in search path..."
	input_file = all_files
all_files.extend(input_file)
all_files = set(all_files)
LoadAllJSON(all_files)

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
# Extract results for each signature
results = map(lambda c: map(partial(JSONExtractor, key = ["elapsed", "time", "m_teps"]), c), collections)
# Sort result by ctime
results = map(lambda r: sorted(r, key=lambda k: time.strptime(k["time"].replace("\n", ""))), results)

PrintResults(sig_dedup, results)

