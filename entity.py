import yaml
import random
from  utils import *


# Segment Class
# holds all the segmentation data
# dimensions, their positions, dim units, distributions)
#

class Segment(object):

    def __init__(self):
        self.dims = []
        self.dim_pos = {}
        self.dim_units = {}
        self.unit_codes = {}
        self.dim_distribution = {}
        return

    #  interprets all the segment config data from a YAML file and puts it in the Segment object
    def load_config(self, config_files):

        yconfig = {}
        for filename in config_files:
            config = yaml.load(open(filename, 'r'))
            merge_dict(yconfig, config)

        pos = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        dims_read = yconfig['dims']

        dims  = [x for x in dims_read if x not in self.dims]

        self.dims = self.dims + dims               # only new dims, prevents duping
        self.dim_pos = dict(zip(self.dims, pos))

        dim_units = {}
        dim_unit_codes = {}
        dim_unit_dist =  {}

        for dim in dims_read:     # Note: dims_read, not dims (only new) - allows over-writing
            units = yconfig[dim]
            ucodes = dict(zip(units,pos[1:]))   # assign units to pos

            dim_units[dim] = units
            dim_unit_codes[dim] = ucodes
            dim_unit_dist[dim] = []

        # if a distribution is specified, set it in the seg scheme
        dists = [k for k in yconfig if k.startswith('dist')]
        for d in dists:
            config = convert_listdict_to_dict(yconfig[d])
            dim = config['dim']
            dim_unit_dist[dim].append(config)

        self.dim_units.update(dim_units)
        self.unit_codes.update(dim_unit_codes)
        self.dim_distribution.update(dim_unit_dist)
        return dims


    #
    # Stuffs a hexbit into a long int at a specific position (counting from right, index 0)
    # Example embed ( 0x0123456789abcdef, 0x7, 3) -> 0x0123456789ab7def
    #
    @staticmethod
    def embed(big_hex, small_hex, pos):
        mask_00f00, mask_ff0ff = Segment.get_masks(pos)
        big_num   = (big_hex & mask_ff0ff)                 # clear big_num at that pos
        small_num = (small_hex << pos * 4) & mask_00f00    # only keep small_num at that pos
        new_num = big_num | small_num                      # bitwise merge (OR) the two nums
        parent = (new_num & mask_ff0ff)                    # Keep the big_num ANY version
        return new_num, parent


    # Returns two masks of the form 0xffffff0fff and 0x0000000f000
    # with the f and 0  at the specified position (pos=0 is rightmost)
    @staticmethod
    def get_masks(pos):
        masker = lambda pos: (0xf << (pos) * 4)
        mask_keep_pos = masker(pos)
        mask_clear_pos = ~mask_keep_pos & 0x7fffffffffffffff
        return mask_keep_pos, mask_clear_pos


    # Given a set of dimensions e,g {'gender':['male'], 'age':['child']}
    # It returns the equivalent segid. Unspecified dimensions are left as 0x0
    def get_segid(self, dims):
        segid = 0x0000000000000000
        for dim in dims:
            dim_unit = dims[dim]
            dim_pos = self.dim_pos[dim]
            dim_unit_code = self.unit_codes[dim][dim_unit]
            segid, parentid = Segment.embed(segid,dim_unit_code,dim_pos)
        return segid


    # Given a segment id  0x0000000000000201
    # it returns the equivalent segment name  t2-male
    # and the dim units {tier:t2, age:unknown, gender:male, }
    def parse_segid(self, segid):
        dict_units = {}
        allhex = segid
        for pos in range(0,len(self.dims)):
            dim = self.dims[pos]
            seg_code = allhex & 0xf
            allhex = allhex >> 4
            unit_code_dict = self.unit_codes[dim]
            unit_matches = [ k for k,v in unit_code_dict.items() if v == seg_code ]
            if len(unit_matches) == 1 :
                dim_unit = unit_matches[0]
                dict_units.update({dim:dim_unit})
        # skip_unk = [x for x in dict_units.values() if x != 'unk']
        skip_unk = dict_units.values()
        unit_str = "-".join(skip_unk) if segid > 0 else "all"
        return (unit_str,dict_units)


#
#  Entity Class
#  Stores mapping of entities to segments
#  in a large array of numbers.  Segments are encoded in hex.
#

class Entity(object):

    def __init__(self, num_entities, entity_size, segment):
        self.num = num_entities
        self.size = entity_size
        self.segment = segment
        self.entities = [0x0] * num_entities  # can be very big, len() = num_entities

    # persist the entity information from a file
    def persist(self, fname):
        write_rows(fname, self.entities)  # TODO rename this to entity.persist
        meta_fname = fname + ".meta"
        seg = self.segment
        data = {'num': self.num, 'size': self.size }
        data.update({'dims':seg.dims, 'dim_pos':seg.dim_pos, 'dim_units':seg.dim_units, 'unit_codes':seg.unit_codes})
        with open(meta_fname, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        return

    # load the entity information from a file
    @staticmethod
    def reload(entity_fname):

        rows = read_rows(entity_fname)

        seg_fname = entity_fname + ".meta"
        config = yaml.load(open(seg_fname, 'r'))
        segment = Segment()
        segment.dims = config['dims']
        segment.dim_pos = config['dim_pos']
        segment.dim_units = config['dim_units']
        segment.unit_codes = config['unit_codes']

        num = int(config['num'])
        siz = int(config['size'])
        entity = Entity(num,siz,segment)
        entity.entities = rows

        return entity

    # Find all the entities that match a segid (fuzzmatch)
    def find_seg (self, segid, candidate_set=None):
        ents = []
        count = 0
        if candidate_set == None:
            candidate_set = range(0,self.num)
        for e in range(0,len(candidate_set)):
            eid = candidate_set[e]
            seg = self.entities[eid]
            if fuzzmatch(segid,seg):
                ents.append(eid)
                count = count + 1
        ent_count = count * self.size
        return (ent_count, count, ents)

    # Ascribe attributes to all the entities as per the segment's distribution data
    def distribute(self, dims=None):
        segment  = self.segment
        dims     = segment.dims if dims is None else dims
        num_ents = self.num
        alldists = segment.dim_distribution

        for dim in dims:                                    # go over each dim
            for dist in segment.dim_distribution[dim] :     # go over each dist in the dim

                cond = dist['cond'] \
                    if 'cond' in dist.keys() \
                    else None                          # if its a conditional dist, get the cond

                mark_set = self.cond_set(cond)         # get list of entities that meet cond
                random.shuffle(mark_set)               # shuffle them so we can divide them randomly
                mark_len = len(mark_set)               # this number of entities that need to be distributed

                for unit,ratio in dist['dist'].items() :   # each dist
                    count = int(ratio * mark_len)          # the count of how many mapped to this unit
                    for i in range(0,count):               # map those many entities in self.entities to segid
                        e = mark_set[i]                    # get the entity
                        segid = self.entities[e]           # retrieve the current segid mapped to this entity
                        self.entities[e] = self.mark(segid,dim,unit)   # a helper fun to assign dim/unit in segid
                    mark_set = mark_set[count:]            # move the pointer forward
                # endfor unit:ratio in each dist[]

            # endfor  dist[]
        # endfor dims
        return

    # Mark the segment-id with the unit_code for (dim,unit)
    def mark(self, segid, dim, unit):
        segment = self.segment
        dim_pos = segment.dim_pos[dim]
        unit_code = segment.unit_codes[dim][unit]
        new_code, parent_code = Segment.embed(segid,unit_code,dim_pos)
        return new_code

    # Retrieve all the entities that match the condition
    def cond_set(self, cond):
        segment = self.segment
        allset = range(0,self.num)
        if cond is None:
            return allset
        newset = []
        for odim,vals in cond.items():
            hexvals = [segment.unit_codes[odim][val] for val in vals ]
            cond[odim] = hexvals
        for e in allset:
            segid = self.entities[e]
            if self.ematch(segid,cond):
                newset.append(e)
        return newset

    #  See if the segid matches the condition e.g (age:[youth,adult])
    def ematch(self,segid, cond):
        segment = self.segment
        ismatch = False
        for dim,hvals in cond.items():
            pos = segment.dim_pos[dim]
            val = (segid >> pos*4) & 0xf
            if val in hvals:
                ismatch = True
        return ismatch
