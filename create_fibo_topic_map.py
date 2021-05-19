import logging
from gastrodon import RemoteEndpoint
import click

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

@click.command()
@click.option('--url',
              default='http://localhost:7200/repositories/FIBO_RL',
              help='URL of SPARQL endpoint containing FIBO')
def load_corpus(url):
    logging.info('SPARQL endpoint: %s' % url)
    rep = RemoteEndpoint(url)
    corpusdf = rep.select('''
select ?iri ?text where { 
?iri ?p ?o.
filter(isiri(?iri))
filter(isliteral(?o))
bind(lcase(str(?o)) as ?text)
}
''')
    logging.info('Query complete %d results' % len(corpusdf))
    return corpusdf

def process_corpus(df):
    pass
    
if __name__ == '__main__':
    process_corpus(load_corpus())
