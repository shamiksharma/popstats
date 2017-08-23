
#
#  Utility helper methods
#
#

# string that shows all 16 hex digits in a long int (eg 0x1234567890abcde )
def hexstr(hex_num):
    return format(hex_num, "#018x")


# rounds up a float to 0.0001
def roundup(fl):
    return int( (fl*10000) + 0.5) / 10000.0


# helper func converts a list-of-dicts (from yaml) to a merged dict
def convert_listdict_to_dict(alist):
    return dict((k, v) for d in alist for (k, v) in d.items())


# helper func merges two dicts d1+d2 -> d1. Its adds up counts of matching keys
def merge_dict(d1,d2):
    for k,v in d2.items():
        if k not in d1.keys():
            d1[k] = v
        else:
            d1[k] = d1[k]+d2[k]
    return d1


# helper func that returns a hexnum that has FFFs  e.g. 0x0000FFF
def fill_0xf(hexnum, size):
    for i in range(0,size):
        hexnum = (hexnum << 4) | 0xf
    return hexnum


# helper func that matches if hex1 hexbits are found-in hex2 .
# Either the hexbits of hex1,hex2 are the same, or hex1 is 0 (unknown)
def fuzzmatch(hex1, hex2):
    result = True
    while hex1 > 0 :
        b1 = hex1 & 0xf
        b2 = hex2 & 0xf
        if (b1 != 0) and (b2 != b1):
            result = False
        hex1 = hex1 >> 4
        hex2 = hex2 >> 4
    return result


# reads all (entities-segment) rfrom a file.
def read_csv(filename) :
    allrows = []
    with open(filename) as csvfile:
     reader = csv.reader(csvfile, delimiter=',')
     for row in reader:
        allrows.append(int(row[0]))  # the row is a single entry, so just pick first
    return allrows

# read a file of ints, one per line. Used to load entity-segment mappings from a file
def read_rows(filename) :
    allrows = []
    f = open(filename,'r')
    for line in f:
        allrows.append(int(line))
    return allrows

# write a large set of ints, one per line. Used to persist entity-seg mappings into a file.
def write_rows(filename, rows):
    f = open(filename, 'wb')
    for row in rows:
        f.write(str(row) + "\n")
    f.flush()
    f.close()
    return

# print a 2-D table of stats, along with row and col headers.
def print_table(rows_of_lists, rownames=[], colnames=[]):

    print "\n%20s\t" % "",
    for col in colnames:
        print "%15s\t" % str(col),
    print ""
    for i in range(0,len(rows_of_lists)):
        if len(rownames) >= i : print "%20s\t" % rownames[i],
        for a in rows_of_lists[i]:
           print "%15s\t" % "{:,}".format(a),
        print ""
