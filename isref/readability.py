# coding: utf-8
from pathlib import Path
import argparse
import datetime
import logging
import os

import numpy as np
import pandas as pd
import plotly.offline as pyo
import plotly.graph_objs as go
import spacy

import helpers as hp


def count_syllables(word):
    """
    Cuenta el numero de sílabas en word.

    Parameters
    ----------
    word: str

    Returns
    -------
    int
    """
    vowels = 'aeiouy'
    word = word.lower()

    # http://phonics.kevinowens.org/syllables.php
    count = len([c for c in word if c in vowels])
    if len(word) > 1:
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] in vowels:
                count -= 1

        if word.endswith('e') and not word.endswith('le'):
            count -= 1

        # este no estaba en regla pero lo encontré
        if word.endswith('ely'):
            count -= 1

    if count < 1:
        count = 1

    return count


def flesch_reading_ease(asl, asxw):
    """
    Calcula el Flesch Reading Ease score.

    Parameters
    ----------
    asl: float (average sentence length)
    asxw: float (average syllables per word)

    Returns
    -------
    float
    """
    # https://en.wikipedia.org/wiki/Flesch-Kincaid_readability_tests
    fre = 206.835 - float(1.015 * asl) - float(84.6 * asxw)

    return round(fre, 2)


def fre_to_grade(fre):
    """
    Traduce el Flesch Reading Ease score a Grade Scale.

    Parameters
    ----------
    fre: float

    Returns
    -------
    str
    """
    # https://en.wikipedia.org/wiki/Flesch-Kincaid_readability_tests
    if fre >= 90:
        score = '5th grade'
    elif fre >= 80:
        score = '6th grade'
    elif fre >= 70:
        score = '7th grade'
    elif fre >= 60:
        score = '8th & 9th grade'
    elif fre >= 50:
        score = '10th to 12th grade'
    elif fre >= 30:
        score = 'College'
    else:
        score = 'College Graduate'

    return score


def flesch_kincaid_grade(asl, asxw):
    """
    Calcula el Flesch Kincaid score.

    Parameters
    ----------
    asl: float (average sentence length)
    asxw: float (average syllables per word)

    Returns
    -------
    float
    """
    # https://en.wikipedia.org/wiki/Flesch-Kincaid_readability_tests
    fkg = float(0.39 * asl) + float(11.8 * asxw) - 15.59

    return round(fkg, 1)


def doc_readability(fpath, lang, other=None):
    """
    Calcula Flesch Reading Ease y Flesch Kincaid de documento en fpath.

    Parameters
    ----------
    fpath: str of Path
    lang: spacy.lang
    other: dict, optional (stopwords, postags, entities, stemmer)

    Returns
    -------
    dict (reading_ease, kincaid_grade, grade, sentences, words)
    """
    nsent, nwords, nsyll = (0, 0, 0)
    text = hp.read_text(fpath)
    doc = lang(text)

    for tokens in hp.doc_sentences(doc, other):
        if tokens:
            nsent += 1
            nwords += len(tokens)
            nsyll += sum(count_syllables(w) for w in tokens)

    try:
        asl = nwords / nsent
    except ZeroDivisionError:
        asl = np.nan

    try:
        asxw = nsyll / nwords
    except ZeroDivisionError:
        asxw = np.nan

    fre = flesch_reading_ease(asl, asxw)
    fkg = flesch_kincaid_grade(asl, asxw)
    grade = fre_to_grade(fre)

    return dict(reading_ease=fre, kincaid_grade=fkg, grade=grade, sentences=nsent, words=nwords)


if __name__ == '__main__':
    description = """Calcula Complejidad del Lenguaje de docs ubicados en dirdocs"""
    parser = argparse.ArgumentParser(description=description)
    desc_dirdocs = "Ubicación de los documentos"
    parser.add_argument("dirdocs", help=desc_dirdocs)
    args = parser.parse_args()

    dir_docs = args.dirdocs

    nlp = spacy.load('en_md')

    dir_corpus = os.path.join(dir_docs, 'corpus')
    dir_output = os.path.join('readability', Path(dir_docs).name)
    dir_logs = os.path.join(dir_output, 'logs')
    os.makedirs(dir_logs, exist_ok=True)

    rundate = f'{datetime.date.today():%Y-%m-%d}'
    logfile = os.path.join(dir_logs, '{}.log'.format(rundate))
    log_format = '%(asctime)s : %(levelname)s : %(message)s'
    log_datefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_format, datefmt=log_datefmt,
                        level=logging.INFO, filename=logfile, filemode='w')

    ents = ['PER', 'ORG']
    extra = dict(entities=ents, )

    scores = []
    for fpath in hp.ordered_filepaths(dir_corpus):
        results = doc_readability(fpath, nlp, extra)
        results['doc'] = fpath.stem
        scores.append(results)

    readability = pd.DataFrame(scores)
    readability.to_csv(os.path.join(dir_output, 'readability.csv'),
                       index=False, encoding='utf-8')

    logging.info(f'Usando documentos en directorio: {Path(dir_docs).name}')
    logging.info(
        f'Complejidad de lenguaje calculada para {len(readability.index)} documentos.')
    logging.info(f'Preprocesamiento usa: {list(extra.keys())}')

   # generar gráfica de Complejidad del Lenguaje
    fechas = pd.to_datetime(readability['doc'], format='%Y-%m-%d')
    kink = readability['kincaid_grade']
    ease = readability['reading_ease']
    grade = readability['grade']

    trace_grade = go.Scatter(x=fechas, y=kink,
                             xaxis='x1', yaxis='y1',
                             line=dict(width=2, color='#9748a1'),
                             marker=dict(size=8, color='#9748a1'),
                             mode='lines+markers',
                             hoverinfo='text',
                             hovertext=[
                                 'Doc: {d:%Y-%m-%d}<br>Kinkaid: {k:.1f}'.format(d=d, k=k) for d, k in zip(fechas, kink)],
                             name='Kincaid Grade')

    trace_ease = go.Scatter(x=fechas, y=ease,
                            xaxis='x2', yaxis='y2',
                            line=dict(width=2, color='#b04553'),
                            marker=dict(size=8, color='#b04553'),
                            mode='lines+markers',
                            hoverinfo='text',
                            hovertext=[
                                 'Doc: {d:%Y-%m-%d}<br>Reading Ease: {r:.2f}<br>Grade: {g}'.format(d=d, r=r, g=g) for d, r, g in zip(fechas, ease, grade)],
                            name='Reading Ease')

    table = go.Table(
        domain=dict(x=[0, 1.0], y=[0, 0.5]),
        columnorder=[0, 1, 2, 3, 4, 5],
        header=dict(values=['<b>{}</b>'.format(c) for c in readability.columns],
                    fill=dict(color='#C2D4FF')
                    ),
        cells=dict(values=[readability[c] for c in readability.columns],
                   fill=dict(color=['#C2D4FF', '#F5F8FF']),
                   format=[None, None, '.1f', '.2f', None, ','],)
    )

    axis = dict(
        showline=True,
        zeroline=True,
        showgrid=True,
        gridcolor='#ffffff',
        automargin=True
    )

    layout = dict(
        autosize=True,
        title='Complejidad de lenguaje en Reportes de Estabilidad Financiera',
        margin=dict(t=100),
        showlegend=True,
        xaxis1=dict(axis, **dict(domain=[0, 0.48], anchor='y1')),
        xaxis2=dict(axis, **dict(domain=[0.52, 1], anchor='y2')),
        yaxis1=dict(
            axis, **dict(domain=[0.55, 1.0], anchor='x1')),
        yaxis2=dict(
            axis, **dict(domain=[0.55, 1.0], anchor='x2')),
        plot_bgcolor='rgba(228, 222, 249, 0.65)'
    )

    fig = dict(data=[trace_grade, trace_ease, table], layout=layout)

    f = os.path.join(dir_output, 'readability.html')
    pltfile = pyo.plot(fig, show_link=False, filename=f, auto_open=False)
