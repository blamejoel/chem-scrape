import requests,datetime,re,sys
from datetime import timedelta
from flask import Flask, request, Response, send_from_directory, url_for, \
        jsonify, make_response, current_app
from functools import update_wrapper
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

sys.path.insert(0, 'lib')
app = Flask(__name__)
# app = Flask(__name__, static_url_path='')


ucr_cal = 'http://registrar.ucr.edu/registrar/academic-calendar/' + \
        'print-academic-calendar.html'


# Cross domain request decorator
def crossdomain(origin=None, methods=None, headers=None, 
                max_age=21600, attach_to_all=True, 
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


# Crappy API
@app.route('/<req_term>')
@crossdomain(origin='*')
def json_output(req_term):
    req_year = request.args.get('year')
    if req_year > 2015:
        search_year = req_year
    else:
        search_year = str(datetime.datetime.now().year)
    term_info = {}
    term_label = 'term'
    start_label = 'start'
    end_label = 'end'
    print req_term + ' ' + search_year
    r = requests.get(ucr_cal)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    col_index = find_term_column(req_term,search_year,soup)
    first_day = find_start_date(soup)
    last_day = find_end_date(soup)
    new_table = reconstruct_table(soup,first_day,last_day)
    term_info[start_label] = convert_date(get_rdate(soup,col_index,1))
    term_info[end_label] = convert_date(get_rdate(soup,col_index,2))
    term_info[term_label] = req_term.upper()
    term_info['year'] = search_year
    return jsonify(**term_info)


# Tabular test
@app.route('/')
def table_output():

    # # Get source
    r = requests.get(ucr_cal)
    html = r.text

    soup = BeautifulSoup(html, "html.parser")

    first_day = find_start_date(soup)
    last_day = find_end_date(soup)

    new_table = reconstruct_table(soup,first_day,last_day)

    return soup.prettify()


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500


# A bunch of functions to do stuff
def find_term_column(quarter,year,soup):
    # Get column for term
    table = soup.find('table')
    col_index = 0
    head_cells = table.tbody.tr.findAll('th')
    for i,cell in enumerate(head_cells):
        if quarter.upper() in cell.string and year in cell.string:
            col_index = i
    return col_index


def find_start_date(soup):
    table = soup.find('table')
    rows = table.tbody.findAll('tr')
    first_day = 0
    last_day = 0
    # Get row for begin instruction
    # print '--- Rows containing days of instruction'
    for i,row in enumerate(rows):
        cells = row.findChildren('td')
        for cell in cells:
            if 'instruction' in cell.string:
                if 'First' in cell.string:
                    first_day = i
                else:
                    last_day = i
    return first_day


def find_end_date(soup):
    table = soup.find('table')
    rows = table.tbody.findAll('tr')
    first_day = 0
    last_day = 0
    # Get row for begin instruction
    # print '--- Rows containing days of instruction'
    for i,row in enumerate(rows):
        cells = row.findChildren('td')
        for cell in cells:
            if 'instruction' in cell.string:
                if 'First' in cell.string:
                    first_day = i
                else:
                    last_day = i
    return last_day


def convert_date(date_str):
    df = '%B %d, %Y'
    do = '%Y-%m-%d'
    if date_str > 1 and bool(re.compile('\d').search(date_str)):
        return datetime.datetime.strptime(date_str, df).strftime(do)
    else:
        return -1


def reconstruct_table(soup,first_day,last_day):
    table = soup.find('table')
    rows = table.tbody.findAll('tr')
    # Reconstruct table with only data we care about
    updated_table = table
    updated_table.tbody.clear()
    updated_table.tbody.append(rows[0])
    updated_table.tbody.append(rows[first_day])
    updated_table.tbody.append(rows[last_day])
    body = soup.find('body')
    body.clear()
    body.append(updated_table)
    head = soup.find('head')
    head.clear()
    return body


def get_rdate(soup,col_index,first_day):
    body = soup.find('body')
    if col_index > 0:
        return  body.table.tbody.findAll('tr')[first_day]\
                .findAll('td')[col_index].string
    else:
        return -1

if __name__ == '__main__':
    app.debug = True
    app.run()
