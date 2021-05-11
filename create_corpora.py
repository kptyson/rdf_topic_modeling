from rdflib import ConjunctiveGraph, Literal, URIRef
import os
import logging
from gastrodon import LocalEndpoint

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    g = ConjunctiveGraph()
    logging.info('Parsing quads')
    g.parse('corpora.nq', format='nquads')
    lep = LocalEndpoint(g)
    logging.info('Corpus query')
    df = lep.select('''
select ?iri ?text where {
    ?iri ?p ?o.
    filter(isliteral(?o))
    bind(lcase(str(?o)) as ?text)
}
''')
    logging.info(len(df))
    df.set_index(['iri']).to_csv('corpus.csv')
    logging.info('Done')
