# Similarity Query Command Line Interface
import sys
import click
import logging
from gastrodon import LocalEndpoint, RemoteEndpoint
from rdflib import ConjunctiveGraph
import pandas as pd
import os
from collections import defaultdict
from gensim import corpora
from gensim import similarities

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

corpus_df = pd.DataFrame()



def gensim_setup(documents):
    # remove common words and tokenize
    stoplist = set('for a of the and to in'.split())
    texts = [
        [word for word in document.lower().split() if word not in stoplist]
        for document in documents
    ]

    # remove words that appear only once
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1

    texts = [
        [token for token in text if frequency[token] > 1]
        for text in texts
    ]

    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    from gensim import models
    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=100)


    # prompt for search term and display similarities
    similarity_results = list()
    while True:
        text = input('Search term: ')
        doc = text.lower()
        vec_bow = dictionary.doc2bow(doc.lower().split())
        vec_lsi = lsi[vec_bow]  # convert the query to LSI space
        index = similarities.MatrixSimilarity(lsi[corpus])  # transform corpus to LSI space and index it
        index.save('tmp/deerwester.index')
        index = similarities.MatrixSimilarity.load('tmp/deerwester.index')
        index.save('tmp/deerwester.index')
        index = similarities.MatrixSimilarity.load('tmp/deerwester.index')
        sims = index[vec_lsi]  # perform a similarity query against the corpus
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        print(list(enumerate(sims))[:10])  # print (document_number, document_similarity) 2-tuples
        for tp in list(enumerate(sims))[:5]:
            ordinal = tp[0]
            document_number = tp[1][0]
            score = tp[1][1]
            text = documents[document_number]
            print('\nordinal: {ord}\ndocnum: {docnum}\nscore: {sco}\ntext: "{t}"\n'.format(ord=ordinal,
                                                                                           docnum=document_number,
                                                                                           sco=score,
                                                                                           t=text))



def populate_corpus(ep, work):
    predicates = ['<%s>' % p for p in work['corpus']]
    query = '''
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?iri ?text WHERE {{
    ?iri {propexpr} ?text.
    FILTER(ISLITERAL(?text))
}}
'''.format(propexpr='|'.join(predicates))
    logging.info('Query: %s' % query)
    global corpus_df
    corpus_df = ep.select(query)


def populate_graph_from_sep(work):
    return populate_corpus(work['sep'], work)


def populate_graph_from_loc(work):
    cg = ConjunctiveGraph()
    for root, dirs, files in os.walk(work['loc']):
        for f in files:
            ftype = f.split('.')[-1]
            if ftype == 'ttl' or ftype == 'rdf':
                logging.info('Parsing: %s' % f)
                cg.parse(os.path.join(root, f), format='xml')
    lep = LocalEndpoint(cg)
    populate_corpus(lep, work)


@click.command()
@click.option('--term', prompt='search term', help='Search term')
@click.option('--sep', help='SPARQL endpoint URL')
@click.option('--loc', help='Directory containing RDF files')
@click.option('--corpus', default='http://www.w3.org/2004/02/skos/core#definition',
              help='IRI of the predicate(s) from which the corpus is constructed.  \
http://www.w3.org/2004/02/skos/core#definition is the default', multiple=True)
def qs(term, sep, loc, corpus):
    if (None is sep and None is loc) or (None is not sep and None is not loc):
        logging.error('Either --loc xor --sep must be specified')
        sys.exit(1)
    click.echo('--term %s' % term)
    click.echo('--sep %s' % sep)
    click.echo('--loc %s' % loc)
    for c in corpus:
        click.echo('--corpus %s' % c)
    work = {
        'term': term,
        'sep': RemoteEndpoint(sep),
        'loc': loc,
        'corpus': corpus
    }

    if loc is not None:
        populate_graph_from_loc(work)
    if sep is not None:
        populate_graph_from_sep(work)
    logging.info('Starting gensim setup')
    gensim_setup([r.text for i, r in corpus_df.iterrows()])


if __name__ == '__main__':
    qs()
    logging.info('Done')
