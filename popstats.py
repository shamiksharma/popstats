from entity import *
from utils  import *
import sys
import itertools
import os


#
# Helper method to split the query into its constituents.
# It would parse #age-gender$t2-female and return  [ [age,gender],  [{tier:t2}{gender:female}]
# SELECT age,gender WHERE tier=t2 and gender=female
#
def splitter(st,entity):
    s = st.split('$')
    seg = s[-1] if len(s) > 1 else ''
    cht = s[0].split('#')[-1]
    segment = entity.segment

    errormsg = "Invalid fields :"
    err_found = False
    cdims=[]
    if cht != '' :
        csplit = cht.split('-')
        for d in csplit:
            if d not in segment.dims:
                errormsg += d + ","
                err_found = True
            else:
                cdims.append(d)
    sdims = []

    if seg == '':
        segs = []
    else :
        seg_list = [a.lstrip('[').rstrip(']').split(',') for a in seg.split('-')]   # make it a list of lists
        # verify that the units are valid, and the dimensions of each
        for units in seg_list:
            units_found = False
            aunit = units[0]
            for d in segment.dims:
                if aunit not in segment.unit_codes[d]: continue
                else:
                    units_found = True
                    sdims.append(d)
                    for unit in units:
                        if unit not in segment.unit_codes[d]:
                            units_found = False
                            aunit = unit
                    break
            if not units_found:
                errormsg += aunit + ","
                err_found = True
                break

        # all possible combos of units (if one of them has many options
        # E.g seg_list = [ [male], [t1,t2] ] -->  [ [male,t1], [male,t2] ]
        allcombos = list(itertools.product(*seg_list))

        # for each unit, specify the dimension  [ {gender:male, tier:t1}, {gender:male, tier:t2} ]
        segs = [dict(zip(sdims, u)) for u in allcombos]

    if  err_found:
        return (False, {'err': errormsg}, {'err': errormsg})
    else:
        return (True, cdims, segs)

# When user types help, returns a list of valid commands
def usage():
    print "\t quit  : exit \n " \
          "\t help  : prints all commands \n " \
          "\t dims  : lists all the dimensions \n\n" \
          "\t create <population> [multiplier] : number of people modelled. Use smaller population with multiplier \n" \
          "\t load  <filename> : load stats from a file \n " \
          "\t save  <filename> : saves the stats in a file \n\n" \
          "\t Queries : \n" \
          "\t $segment1-segment2-...  : get the count of people that match the specified segments \n" \
          "\t #dimensionX$segment1-segment2 : print the distribution of a dimension for people who match the specified segments\n\n" \
          "\t Sample queries : #age, $female-youth-t2,  #age-gender$t2,  #age$female-t1 \n "


# the main interpreter command loop.
# we can pass it an initial set of comamnds
# These will be executed before asking for user-input

def cmdLoop(init_cmds):

    cmds = init_cmds

    while True:  # infinite loop
        if len(cmds) == 0 :
            cmd = raw_input("> ")
        else :
            cmd = cmds.pop(0)
            print "> " + cmd

        if cmd == "":
            continue
        elif cmd in ['quit', 'exit', 'Q', 'q']:
            break
        elif cmd.startswith("help"):
            usage()
            continue
        elif cmd.startswith("create"):
            entry = cmd.lstrip("create").strip().split(',')
            entries = [x.strip() for x in entry]
            num_entities = int(entries[0])
            entity_size  = int(entries[1]) if len(entries) > 1 else 1
            people = Entity(num_entities, entity_size, Segment())
            print "Created %d entities (%d x %d)" % ((people.num * people.size), people.num,people.size)

        elif cmd.startswith("load"):
            entity_fname = cmd.lstrip("load").strip()
            if not os.path.exists(entity_fname)  :
                print "Invalid filename : %s " % entity_fname
                continue
            try :
                people = Entity.reload(entity_fname)
            except Exception:
                print "Error in reading file"
                continue
            print "Loaded %d entities" % num_entities
        elif cmd.startswith("dims"):
            print "Dimensions : %s " % people.segment.dims
            for dim in people.segment.dims:
                print "%10s : %s" %  (dim, people.segment.dim_units[dim])
            continue
        elif cmd.startswith("save"):
            fname = cmd.lstrip("save").strip()
            if fname == "" :
                print "Specify a filename ( > save file-name ) "
                continue
            people.persist(fname)
            print "Saved entities in file %s " % (fname)
            continue
        elif cmd.startswith("add"):
            filenames = cmd.lstrip("add").strip().split(',')
            fnames = [x.strip() for x in filenames]
            dims = people.segment.load_config(fnames)
            people.distribute(dims)
            print "Added dims : %s" % (dims)
            if len(dims) != len(people.segment.dims) :
                print "Dimensions : %s " % people.segment.dims
            continue
        else:                  # the main query executing logic
            isvalid, chart, segs  = splitter(cmd,people)
            if  not isvalid:
                print chart['err']
                continue

            segment = people.segment

            sum = 0
            candidate_set = []
            if len(segs) == 0 :
                candidate_set = range(0,people.num)
            for seg in segs:
                segid = segment.get_segid(seg)
                segname, units = segment.parse_segid(segid)
                ecount, raw_num, ppl = people.find_seg(segid)
                candidate_set = list(set(candidate_set + ppl))
                sum += ecount
                print "%20s\t : %15s " % (segname, "{:,}".format(ecount))
                # print "%20s\t : %d  (%d) " % ("Sum is : ", sum, len(candidate_set))
            if len(segs) > 1 :
                print "%20s\t : %15s  \n" % ("Sum is ", "{:,}".format(sum))

            if len(chart) >= 1:
                row_dim = chart[0]
                row_units = segment.dim_units[row_dim]
                if len(chart) >= 2 :
                    col_dim = chart[1]
                    col_units = segment.dim_units[col_dim]
                else:
                    col_dim = 'all'
                    col_units = ['']

                counts = []
                for i in range(0,len(row_units)):
                    counts.append([0]*len(col_units))
                    for j in range(0,len(col_units)):
                        seg = {row_dim:row_units[i]}
                        if  col_dim != 'all' :  seg.update( {col_dim:col_units[j]} )
                        segid = segment.get_segid(seg)
                        segname, units = segment.parse_segid(segid)
                        ecount, raw_num, ppl = people.find_seg(segid, candidate_set)
                        counts[i][j] = ecount

                print_table(counts,row_units,col_units)
    return


def main(argv=None):
    init_cmds = ["create 100000, 13500", "add config-asl.yml", "add config-income.yml"]
    cmdLoop(init_cmds)

if __name__ == "__main__":
    sys.exit(main())




