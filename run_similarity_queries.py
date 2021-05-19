import logging

import pandas as pd

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

from collections import defaultdict
from gensim import corpora

#
# KPT: Populate 'documents' from skos:definition in FIBO
#
from gastrodon import RemoteEndpoint

rep = RemoteEndpoint('http://localhost:7200/repositories/FIBO_RL')

search_terms_df = rep.select('''
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?iri ?text WHERE {
    ?iri rdfs:label ?text.
}
''')
search_terms_df.to_csv('SearchTerms1.csv')
search_terms_df['text'] = search_terms_df['text'].str.lower()
search_terms_df.to_csv('SearchTerms2.csv')

documents_df = rep.select('''
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?iri ?text WHERE {
    ?iri rdfs:label ?text.
}''')
documents_df['text'] = documents_df['text'].str.lower()

documents = [r.text for i, r in documents_df.iterrows()]

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
lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=25)


doc = "credit"
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lsi = lsi[vec_bow]  # convert the query to LSI space

from gensim import similarities
index = similarities.MatrixSimilarity(lsi[corpus])  # transform corpus to LSI space and index it

index.save('tmp/deerwester.index')
index = similarities.MatrixSimilarity.load('tmp/deerwester.index')

sims = index[vec_lsi]  # perform a similarity query against the corpus

sims = sorted(enumerate(sims), key=lambda item: -item[1])

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
img = mpimg.imread('run_similarity_queries.png')
imgplot = plt.imshow(img)
_ = plt.axis('off')

print('Here we go')
similarity_results = list()
for i, r in search_terms_df.iterrows():
    doc = r.text
    vec_bow = dictionary.doc2bow(doc.lower().split())
    vec_lsi = lsi[vec_bow]  # convert the query to LSI space
    sims = index[vec_lsi]  # perform a similarity query against the corpus
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    for doc_position, doc_score in sims:
        similarity_results.append((r.iri, r.text, doc_score, documents[doc_position]))
sdf = pd.DataFrame(similarity_results, columns=['iri', 'term', 'score', 'similar text']).sort_values(['iri']).set_index(['iri'])
sdf.to_csv('similarity_results.csv')
print('Done')

