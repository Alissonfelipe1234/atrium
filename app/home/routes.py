from app.home import blueprint
from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound

import pathlib
import pandas as pd
import numpy as np

precos = pd.read_feather('cache/precos.feather')
inflation = pd.read_feather('cache/inflation.feather')
precos_mes = precos[precos['DATA'] == pd.Timestamp(2020, 8, 1)].dropna(subset=['SUBSTANCIA'])

@blueprint.route('/index')
def index():
    return render_template('index.html')

@blueprint.route('/search')
def search():
    global precos_mes

    query = request.args.get('q', '').upper()
    results = precos_mes.query('SUBSTANCIA.str.contains(@query) or PRODUTO.str.contains(@query)', engine='python')
    results['MAX'] = results['MAX'].fillna('Sem controle')
    query = query.capitalize()
    
    return render_template('search.html', query=query, results=results)

@blueprint.route('/info')
def info():
    global precos, precos_mes

    id = request.args.get('id', '')
    result = precos.query('GGREM == @id', engine='python')

    variation = round(get_percentage(result.head(1)['MAX'].iloc[0], result.tail(1)['MAX'].iloc[0]), 2)
    correlation = round(result.reset_index()['MIN'].corr(inflation['inflation']), 2)

    substancia = result.SUBSTANCIA.iloc[0]
    factory = result.LABORATORIO.iloc[0]
    similar = precos_mes.loc[precos_mes.SUBSTANCIA.str.contains(substancia, na=False)]
    
    similar_todos = precos.loc[precos.SUBSTANCIA.str.contains(substancia, na=False)]
    same_factory_todos = precos.loc[precos.LABORATORIO == factory]

    similar_todos_mean = similar_todos.groupby('DATA')['MIN'].mean().reset_index(drop=True)
    same_factory_todos_mean = same_factory_todos.groupby('DATA')['MIN'].mean().reset_index(drop=True)

    correlation_similar = round(similar_todos_mean.corr(inflation['inflation']), 2)
    correlation_factory = round(same_factory_todos_mean.corr(inflation['inflation']), 2)

    similar_less = similar.sort_values(by=['MIN']).head(1)['MIN'].iloc[0]
    similar_more = similar.sort_values(by=['MAX']).dropna(subset=['MAX']).tail(1)['MAX'].iloc[0]
    
    data = {
        "similar": similar,
        "inflation": inflation,
        "correlation": correlation,
        "correlation_similar": correlation_similar,
        "correlation_factory": correlation_factory,
        "similar_todos_mean": similar_todos_mean,
        "same_factory_todos_mean": same_factory_todos_mean,
        "variation": variation,
        "similar_less": similar_less,
        "similar_more": similar_more
    }
    return render_template('info.html', result=result, data=data)

@blueprint.route('/panel')
def panel():
    global precos, precos_mes

    total = precos_mes.shape[0]
    tarjas = precos_mes.groupby('TARJA')['SUBSTANCIA'].count()
    tarjas_porcentage = tarjas.apply(get_totals_percentage, args=(precos_mes.shape[0],))
    means = precos.dropna(subset=['MAX']).groupby('DATA')[['MAX', 'MIN']].mean().apply(rounttwo)
    data = {
        'total': total,
        'tarjas': tarjas,
        'tarjas_porcentage': tarjas_porcentage,
        'means': means
    }

    return render_template('panel.html', data=data)


@blueprint.route('/<template>')
def route_template(template):
    query = request.args.get('q', '')
    try:
        return render_template(template + '.html')

    except TemplateNotFound:
        return render_template('page-404.html', query=query), 404
    
    except:
        return render_template('page-500.html'), 500

def get_percentage(current, previous):
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0

def get_totals_percentage(current, totals):
    try:
        return round((current * 100)/totals, 2)
    except ZeroDivisionError:
        return 0

def rounttwo(num):
    return round(num, 2)