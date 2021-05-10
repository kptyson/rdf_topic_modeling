from rdflib import ConjunctiveGraph
import os
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    g = ConjunctiveGraph()
    for root, dirs, files in os.walk('input'):
        for f in files:
            fspec = os.path.join(root, f)
            if 'rdf' != f.split('.')[-1]:
                continue
            logging.info('Parsing: %s' % fspec)
            g.parse(fspec, format='rdf')
    logging.info('Serializing corpora')
    g.serialize('corpora.nq', format='nquads')
    logging.info('Done')
