"""
search alternative codonpositions due to different transcript usage
"""
import sys, re, argparse
from mutation import parser_add_mutation, parse_tok_mutation_str, list_parse_mutation
from transcripts import *
from utils import *
from config import read_config
from snv import __core_annotate_codon_snv
from record import Query, QueryREG

outformat="{altid}\t{chrm}\t{codon1}\t{codon2}\t{tptstr}"

def _main_core_(args, q, db):

    k2transcripts = {}
    if isinstance(q, QueryREG):
        q.pos = q.beg
        q.ref = q.refseq
        q.alt = ''

    for t1, c1 in __core_annotate_codon_snv(args, q, db):
        # search any of the 3 positions
        for cind in xrange(3):
            gpos = c1.locs[cind]
            for t2 in db.get_transcripts(t1.chrm, gpos):
                c2, p = t2.gpos2codon(gpos)
                if t1 == t2: continue
                if p.tpos != 0: continue
                # if c2.region != 'coding': continue
                if c1.index == c2.index: continue
                if len(c2.seq) != 3: continue # often due to last incomplete codon
                if q.ref and q.ref != codon2aa(c2.seq): continue
                altid = t1.gene.name+'.p.'
                if q.ref: altid += q.ref
                altid += str(c2.index)
                k = (altid, c1.chrm, tuple(c1.locs), tuple(c2.locs))
                tpair = '%s[%s]/%s[%s]' % (t1.name, t1.source, t2.name, t2.source)
                if k in k2transcripts:
                    if tpair not in k2transcripts[k]:
                        k2transcripts[k].append(tpair)
                else:
                    k2transcripts[k] = [tpair]

    for k, tpairs in k2transcripts.iteritems():
        altid, chrm, c1, c2 = k
        if q.op: s = q.op+'\t'
        else: s = ''
        s += outformat.format(altid=altid, tptstr=','.join(tpairs), chrm=chrm,
                              codon1='-'.join(map(str,c1)), codon2='-'.join(map(str,c2)))
        print s

def main_list(args, db): #name2gene, thash):

    for q, line in list_parse_mutation(args):

        q.gene = db.get_gene(q.tok)
        if not q.gene:
            sys.stderr.write("Gene %s is not recognized.\n" % q.tok)
            continue
        # if q.tok not in name2gene:
        #     sys.stderr.write("Gene %s is not recognized.\n" % q.tok)
        #     continue
        # q.gene = name2gene[q.tok]
        try:
            _main_core_(args, q, db)
        except UnImplementedError as e:
            err_print(line)
            raise e
        except SequenceRetrievalError as e:
            err_print(line)
            raise e

def main_one(args, db): #name2gene, thash):

    q = parse_tok_mutation_str(args.i)
    q.op = args.i
    q.gene = db.get_gene(q.tok)
    if not q.gene:
        sys.stderr.write("Gene %s not recognized.\n" % q.tok)
        return

    # if q.tok not in name2gene:
    #     sys.stderr.write("Gene %s not recognized.\n" % q.tok)
    #     return
    # q.gene = db.name2gene[q.tok]
    q.op = args.i

    _main_core_(args, q, db)

def main(args):

    config = read_config()
    db = AnnoDB(args, config)
    # name2gene, thash = parse_annotation(args)

    if args.l:
        main_list(args, db) #name2gene, thash)
    if args.i:
        main_one(args, db) #name2gene, thash)

def add_parser_codonsearch(subparsers, config):

    parser = subparsers.add_parser('codonsearch', help=__doc__)
    parser_add_mutation(parser)
    parser_add_annotation(parser)
    parser.set_defaults(func=main)