import os
from ppaxe import core
from ppaxe import report
import re
import smtplib
import mail
from ppaxe import PubMedQueryError
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash


app = Flask(__name__) # create the application instance
app.config.from_object(__name__) # load config from this file


@app.route('/', methods=['GET', 'POST'])
def home_form():
    '''
    Home of the ppaxe web application containing the form
    '''
    identifiers  = str()
    database     = str()
    results      = None
    nints        = None
    nprots       = None
    sum_table    = None
    int_table    = None
    prot_table   = None
    graph        = None
    error        = None
    plots        = dict()
    if 'identifiers' in request.form:
        # Get Form parameters
        identifiers = request.form['identifiers']
        database = request.form['database']
        email = request.form['email']
        identifiers = re.split(",|\n|\r", identifiers)
        identifiers = [ident for ident in identifiers if ident]
        #identifiers = identifiers.split(",")

        # Get articles from Pubmed or PMC
        source = str()
        try:
            query = core.PMQuery(ids=identifiers, database=database)
            query.get_articles()
        except PubMedQueryError:
            error = "PMQuery"
            return render_template('home.html',
                                    error=error,
                                    identifiers=identifiers,
                                    prot_table=prot_table,
                                    sum_table=sum_table,
                                    int_table=int_table,
                                    nints=nints,
                                    nprots=nprots,
                                    graph=graph,
                                    plots=plots,
                                    database=database)

        # Retrieve interactions from 'source'
        if database == "PUBMED":
            source = "abstract"
        else:
            source = "fulltext"
        for article in query.articles:
            article.predict_interactions(source)

        summary = report.ReportSummary(query)
        summary.graphsummary.makesummary()
        summary.protsummary.makesummary()
        nints  = summary.graphsummary.numinteractions
        nprots = summary.protsummary.totalprots
        if nints > 0:
            # Tables
            int_table = summary.graphsummary.table_to_html()
            sum_table = summary.summary_table()
            # JSON graph
            graph     = summary.graphsummary.graph_to_json()
            # Plots
            plots['j_int_plot'], plots['j_prot_plot'], plots['a_year_plot'] = summary.journal_plots()
            plots['j_prot_plot'] = plots['j_prot_plot'].getvalue().encode("base64").strip()
            plots['j_int_plot']  = plots['j_int_plot'].getvalue().encode("base64").strip()
            plots['a_year_plot'] = plots['a_year_plot'].getvalue().encode("base64").strip()
        if nprots > 0:
            prot_table = summary.protsummary.table_to_html()
        else:
            nprots = 0

        if email:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            #Next, log in to the server
            server.login("ppaxeatcompgen", mail.passw)
            msg = "Hello THERE BEAUTIFUL!"
            server.sendmail("ppaxeatcompgen@gmail.com", email, msg)

    return render_template('home.html',
                            identifiers=identifiers,
                            prot_table=prot_table,
                            sum_table=sum_table,
                            int_table=int_table,
                            nints=nints,
                            nprots=nprots,
                            graph=graph,
                            plots=plots,
                            database=database)

@app.route('/tutorial', methods=['GET'])
def tutorial():
    '''
    Tutorial page
    '''
    return render_template('tutorial.html')

@app.route('/about', methods=['GET'])
def about():
    '''
    About page
    '''
    return render_template('about.html')
