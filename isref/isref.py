# coding: utf-8
from collections import Counter
from pathlib import Path
import argparse
import datetime
import json
import logging
import os

import numpy as np
import pandas as pd
import plotly.offline as pyo
import plotly.graph_objs as go
import spacy

import helpers as hp


def fss(tokens, pos, neg):
    """
    Calcula Financial Stability Sentiment index basado en tokens de un documento.

    Parameters
    ----------
    tokens: list or iterable
    pos: set
    neg: set

    Yields
    ------
    float
    """
    fd = Counter(tokens)

    emopos = sum(c for w, c in fd.items() if w in pos)
    emoneg = sum(c for w, c in fd.items() if w in neg)
    total = sum(fd.values())

    emodiff = emoneg - emopos

    try:
        score = (emodiff / total)
    except ZeroDivisionError:
        score = np.nan
    except Exception as e:
        score = np.nan
        logging.info('ERROR inesperado calculando FSS: {}'.format(e))

    return score


def score_doc(fpath, pos, neg, lang, other=None):
    """
    Calcula Financial Stability Sentiment index de un documento en fpath.

    Parameters
    ----------
    fpath: str or Path
    pos: list or set or iterable
    neg: list or set or iterable
    lang: spacy.lang
    other: dict, optional (stopwords, postags, entities, stemmer)

    Returns
    -------
    float
    """
    text = hp.read_text(fpath)
    doc = lang(text)

    words = []
    for tokens in hp.doc_sentences(doc, other):
        words.extend(tokens)

    return fss(words, pos, neg)


if __name__ == '__main__':
    description = """Calcula ISREF de docs ubicados en dirdocs"""
    parser = argparse.ArgumentParser(description=description)
    desc_dirdocs = "Ubicación de los documentos"
    parser.add_argument("dirdocs", help=desc_dirdocs)
    desc_wdfile = "Ubicación de archivo json de palabras positivas y negativas"
    parser.add_argument("wdfile", help=desc_wdfile)
    desc_stopsfile = "Ubicación de archivo excel de palabras a ignorar (stopwords)"
    parser.add_argument("stopsfile", help=desc_stopsfile)
    args = parser.parse_args()

    dir_docs = args.dirdocs
    wdlist = args.wdfile
    pathstops = args.stopsfile

    nlp = spacy.load('en_md')

    dir_corpus = os.path.join(dir_docs, 'corpus')
    dir_output = os.path.join('isref', Path(dir_docs).name)
    dir_logs = os.path.join(dir_output, 'logs')
    os.makedirs(dir_logs, exist_ok=True)

    rundate = f'{datetime.date.today():%Y-%m-%d}'
    logfile = os.path.join(dir_logs, '{}.log'.format(rundate))
    log_format = '%(asctime)s : %(levelname)s : %(message)s'
    log_datefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_format, datefmt=log_datefmt,
                        level=logging.INFO, filename=logfile, filemode='w')

    with open(wdlist, encoding='utf-8') as f:
        diction = json.load(f, encoding='utf-8')

    positive = diction.get('positive')
    negative = diction.get('negative')

    # opciones para incluir en extra
    # stemmer=SnowballStemmer('spanish')
    # habiendo importado from nltk.stem import SnowballStemmer
    # (stopwords=stops, entities=ents, postags=tags, stemmer=stemmer)

    #tags = ['NOUN', 'VERB', 'ADJ', 'ADV', 'ADP','AUX', 'DET', 'PRON']
    stops = hp.load_stopwords(pathstops, 'english', col='word')
    ents = ['PER', 'ORG']
    extra = dict(stopwords=stops, entities=ents, )

    scores = []
    for fpath in hp.ordered_filepaths(dir_corpus):
        result = {}
        score = score_doc(fpath, positive, negative, nlp, extra)
        result['score'] = score
        result['doc'] = fpath.stem
        scores.append(result)

    isref = pd.DataFrame(scores)
    isref.dropna(subset=['score'], inplace=True)
    isref.to_csv(os.path.join(dir_output, 'isref.csv'),
                 index=False, encoding='utf-8')

    logging.info(f'Usando documentos en directorio: {Path(dir_docs).name}')
    logging.info(f'Usando archivo de palabras: {Path(wdlist).name}')
    logging.info(f'ISREF calculado para {len(isref.index)} documentos.')

    # generar gráfica del ISREF
    fechas = pd.to_datetime(isref['doc'], format='%Y-%m-%d')

    axis = dict(
        showline=True,
        zeroline=True,
        showgrid=True,
        gridcolor='#ffffff',
        automargin=True
    )

    trace = go.Scatter(x=fechas, y=isref['score'],
                       line=dict(width=2, color='#b04553'),
                       marker=dict(size=8, color='#b04553'),
                       name='ISREF')

    layout = dict(title='Sentimiento de Reportes de Estabilidad Financiera',
                  width=800, height=600,
                  xaxis=dict(axis, **dict(title='Fecha')),
                  yaxis=dict(axis, **dict(title='ISREF', hoverformat='.3f')),
                  showlegend=False,
                  autosize=True,
                  plot_bgcolor='rgba(228, 222, 249, 0.65)'
                  )

    fig = dict(data=[trace], layout=layout)
    filename = os.path.join(dir_output, 'isref.html')
    plturl = pyo.plot(fig, show_link=False, filename=filename, auto_open=False)
