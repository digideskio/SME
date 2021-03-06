#! /usr/bin/python
import sys
from model import *

def load_file(path):
    return scipy.sparse.csr_matrix(cPickle.load(open(path)),
            dtype=theano.config.floatX)

def parseline(line):
    lhs, rel, rhs, v = line.split('\t')
    lhs = [lhs] #.split(' ')
    rhs = [rhs] #.split(' ')
    rel = [rel] #.split(' ')
    v = float(v)
    return lhs, rel, rhs, v

def convert2idx(spmat):
    rows, cols = spmat.nonzero()
    return rows[np.argsort(cols)]

def write_predictions(preds, file):
    """
    Write out the test predictions into a file.
    :return: None
    """
    print "Sorting"
    arr = sorted(preds, key=lambda student: student[0], reverse=True)
    print "Writing to " + file
    f = open(file, 'w')
    for a in arr:
        f.write('{score:f}\t{e1}\t{e2}\t{val}\t{rel}\n'.format(score=a[0], e1=a[1], e2=a[2], val=a[3], rel=a[4]))
    f.close

def naaclEval(datapath='./data/', synset2Idxfile='NAACL_entity2idx.pkl', 
        testTriplets="./NAACL/naacl-triplet-test.txt", loadmodel='best_valid_model.pkl',
        idx2synsetfile='NAACL_idx2entity.pkl', synset2idxfile='NAACL_entity2idx.pkl', 
        outfile='./NAACL/preds.txt', Nsyn=24518):
    # Load model
    f = open(loadmodel)
    embeddings = cPickle.load(f)
    leftop = cPickle.load(f)
    rightop = cPickle.load(f)
    simfn = cPickle.load(f)
    f.close()

    ranklfunc = RankLeftFnIdx(simfn, embeddings, leftop, rightop,
            subtensorspec=Nsyn)
    rankrfunc = RankRightFnIdx(simfn, embeddings, leftop, rightop,
            subtensorspec=Nsyn)
    rankfunc = RankRelFnIdx(simfn, embeddings, leftop, rightop,subtensorspec=Nsyn)

    name2Idx = cPickle.load(open(datapath + synset2idxfile))
    mainIdx = cPickle.load(open(datapath + idx2synsetfile))
    print "name2Idx: ", len(name2Idx)
    print "mainIdx: ", len(mainIdx)

    f = open(testTriplets, 'r')
    dat = f.readlines()
    f.close()
    preds = []
    for i in dat:
        lhs, rel, rhs, v = parseline(i[:-1])
        if lhs[0] in name2Idx and rhs[0] in name2Idx and rel[0] in name2Idx: 
            idxl=name2Idx[lhs[0]]
            idxr=name2Idx[rhs[0]]
            idxo=name2Idx[rel[0]]
            result=rankfunc(idxl, idxr)
            score=result[0][idxo-Nsyn]
            preds.append((score, lhs[0], rhs[0], str(v), rel[0]))
    write_predictions(preds, outfile)

def RankingEval(datapath='./data/', dataset='NAACL-test',
        loadmodel='best_valid_model.pkl', neval='all', Nsyn=24518, n=10):

    # Load model
    f = open(loadmodel)
    embeddings = cPickle.load(f)
    leftop = cPickle.load(f)
    rightop = cPickle.load(f)
    simfn = cPickle.load(f)
    f.close()

    # Load data
    l = load_file(datapath + dataset + '-lhs.pkl')
    r = load_file(datapath + dataset + '-rhs.pkl')
    o = load_file(datapath + dataset + '-rel.pkl')
    if type(embeddings) is list:
        o = o[-embeddings[1].N:, :]

    # Convert sparse matrix to indexes
    if neval == 'all':
        idxl = convert2idx(l)
        idxr = convert2idx(r)
        idxo = convert2idx(o)
    else:
        idxl = convert2idx(l)[:neval]
        idxr = convert2idx(r)[:neval]
        idxo = convert2idx(o)[:neval]

    ranklfunc = RankLeftFnIdx(simfn, embeddings, leftop, rightop,
            subtensorspec=Nsyn)
    rankrfunc = RankRightFnIdx(simfn, embeddings, leftop, rightop,
            subtensorspec=Nsyn)

    rankfunc = RankRelFnIdx(simfn, embeddings, leftop, rightop,subtensorspec=Nsyn)
    res = RankingScoreIdx(ranklfunc, rankrfunc, idxl, idxr, idxo)
    dres = {}
    dres.update({'microlmean': np.mean(res[0])})
    dres.update({'microlmedian': np.median(res[0])})
    dres.update({'microlhits@n': np.mean(np.asarray(res[0]) <= n) * 100})
    dres.update({'micrormean': np.mean(res[1])})
    dres.update({'micrormedian': np.median(res[1])})
    dres.update({'microrhits@n': np.mean(np.asarray(res[1]) <= n) * 100})
    resg = res[0] + res[1]
    dres.update({'microgmean': np.mean(resg)})
    dres.update({'microgmedian': np.median(resg)})
    dres.update({'microghits@n': np.mean(np.asarray(resg) <= n) * 100})

    print "### MICRO:"
    print "\t-- left   >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['microlmean'], 5), round(dres['microlmedian'], 5),
            n, round(dres['microlhits@n'], 3))
    print "\t-- right  >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['micrormean'], 5), round(dres['micrormedian'], 5),
            n, round(dres['microrhits@n'], 3))
    print "\t-- global >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['microgmean'], 5), round(dres['microgmedian'], 5),
            n, round(dres['microghits@n'], 3))

    listrel = set(idxo)
    dictrelres = {}
    dictrellmean = {}
    dictrelrmean = {}
    dictrelgmean = {}
    dictrellmedian = {}
    dictrelrmedian = {}
    dictrelgmedian = {}
    dictrellrn = {}
    dictrelrrn = {}
    dictrelgrn = {}

    for i in listrel:
        dictrelres.update({i: [[], []]})

    for i, j in enumerate(res[0]):
        dictrelres[idxo[i]][0] += [j]

    for i, j in enumerate(res[1]):
        dictrelres[idxo[i]][1] += [j]

    for i in listrel:
        dictrellmean[i] = np.mean(dictrelres[i][0])
        dictrelrmean[i] = np.mean(dictrelres[i][1])
        dictrelgmean[i] = np.mean(dictrelres[i][0] + dictrelres[i][1])
        dictrellmedian[i] = np.median(dictrelres[i][0])
        dictrelrmedian[i] = np.median(dictrelres[i][1])
        dictrelgmedian[i] = np.median(dictrelres[i][0] + dictrelres[i][1])
        dictrellrn[i] = np.mean(np.asarray(dictrelres[i][0]) <= n) * 100
        dictrelrrn[i] = np.mean(np.asarray(dictrelres[i][1]) <= n) * 100
        dictrelgrn[i] = np.mean(np.asarray(dictrelres[i][0] +
                                           dictrelres[i][1]) <= n) * 100

    dres.update({'dictrelres': dictrelres})
    dres.update({'dictrellmean': dictrellmean})
    dres.update({'dictrelrmean': dictrelrmean})
    dres.update({'dictrelgmean': dictrelgmean})
    dres.update({'dictrellmedian': dictrellmedian})
    dres.update({'dictrelrmedian': dictrelrmedian})
    dres.update({'dictrelgmedian': dictrelgmedian})
    dres.update({'dictrellrn': dictrellrn})
    dres.update({'dictrelrrn': dictrelrrn})
    dres.update({'dictrelgrn': dictrelgrn})

    dres.update({'macrolmean': np.mean(dictrellmean.values())})
    dres.update({'macrolmedian': np.mean(dictrellmedian.values())})
    dres.update({'macrolhits@n': np.mean(dictrellrn.values())})
    dres.update({'macrormean': np.mean(dictrelrmean.values())})
    dres.update({'macrormedian': np.mean(dictrelrmedian.values())})
    dres.update({'macrorhits@n': np.mean(dictrelrrn.values())})
    dres.update({'macrogmean': np.mean(dictrelgmean.values())})
    dres.update({'macrogmedian': np.mean(dictrelgmedian.values())})
    dres.update({'macroghits@n': np.mean(dictrelgrn.values())})

    print "### MACRO:"
    print "\t-- left   >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['macrolmean'], 5), round(dres['macrolmedian'], 5),
            n, round(dres['macrolhits@n'], 3))
    print "\t-- right  >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['macrormean'], 5), round(dres['macrormedian'], 5),
            n, round(dres['macrorhits@n'], 3))
    print "\t-- global >> mean: %s, median: %s, hits@%s: %s%%" % (
            round(dres['macrogmean'], 5), round(dres['macrogmedian'], 5),
            n, round(dres['macroghits@n'], 3))

    return dres


if __name__ == '__main__':
    naaclEval(loadmodel=sys.argv[1])
    RankingEval(loadmodel=sys.argv[1])
