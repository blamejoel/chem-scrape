import requests,datetime,re,sys,json
from datetime import timedelta
from flask import Flask, request, Response, send_from_directory, url_for, \
        jsonify, make_response, current_app
from functools import update_wrapper
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

sys.path.insert(0, 'lib')
app = Flask(__name__)
# app = Flask(__name__, static_url_path='')


base_pub = 'https://pubchem.ncbi.nlm.nih.gov/compound/'
base_pub2 = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'
base_ncbi = 'https://www.ncbi.nlm.nih.gov/'
c_search_path = 'pccompound?term='
headers = {'user-agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; \
rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'}


compound = 'Nitropyrene'


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
@app.route('/<req_compound>')
@crossdomain(origin='*')
def json_output(req_compound):
    req_num = int(request.args.get('num', 0, type=int))
    cid = getPubChemID(req_compound, req_num)
    url2get = base_pub2 + cid + '/JSON/'
    print url2get
    r = requests.get(url2get, headers=headers)
    html = r.text
    soup = BeautifulSoup(html, "html5lib")
    result_data = json.loads(r.content)
    json_output = {}

    # # Melting Point
    # if 'Melting Point' in r.text:
    json_output['Melting Point'] = []
    json_output['Boiling Point'] = []
    json_output['Freezing Point'] = []
    json_output['Chemical/Compound'] = ''
    json_output['Reaction Group ID'] = ''


    # PubChem ID
    json_output['PubChecm ID'] = result_data['Record']['RecordNumber']

    sections = result_data['Record']['Section']
    names_and_id = get_depth('Names and Identifiers', sections)
    chem_phys_props = get_depth('Chemical and Physical Properties', sections)
    sections = result_data['Record']['Section'][names_and_id]['Section']
    record_title = get_depth('Record Title', sections)
    computed_desc = get_depth('Computed Descriptors', sections)
    other_id = get_depth('Other Identifiers', sections)
    id_sections = result_data['Record']['Section'][names_and_id]['Section'][other_id]['Section']
    synonyms = get_depth('Synonyms', sections)
    syn_sections = result_data['Record']['Section'][names_and_id]['Section'][synonyms]['Section']

    json_output['name'] = result_data['Record']['Section'][names_and_id]['Section'][record_title]['Information'][0]['StringValue']

    computed_sections = result_data['Record']['Section'][names_and_id]['Section'][computed_desc]['Section']
    if 'InChI Key' in r.text:
        inchi_key_sec = get_depth('InChI Key', computed_sections)
        json_output['InChI-key'] = result_data['Record']['Section'][names_and_id]['Section'][computed_desc]['Section'][inchi_key_sec]['Information'][0]['StringValue']
    else:
        json_output['InChI-key'] = ''
    if 'Canonical SMILES' in r.text:
        c_smiles_sec = get_depth('Canonical SMILES', computed_sections)
        json_output['Canonical SMILES'] = result_data['Record']['Section'][names_and_id]['Section'][computed_desc]['Section'][c_smiles_sec]['Information'][0]['StringValue']
    else:
        json_output['Canonical SMILES'] = ''
    if 'Isomeric SMILES' in r.text:
        i_smiles_sec = get_depth('Isomeric SMILES', computed_sections)
        json_output['Isomeric SMILES'] = result_data['Record']['Section'][names_and_id]['Section'][computed_desc]['Section'][i_smiles_sec]['Information'][0]['StringValue']
    else:
        json_output['Isomeric SMILES'] = ''
    if 'Molecular Formula' in r.text:
        molecular_form = get_depth('Molecular Formula', sections)
        json_output['molecular-formula'] = result_data['Record']['Section'][names_and_id]['Section'][molecular_form]['Information'][0]['StringValue']
    else:
        json_output['molecular-formula'] = ''
    if 'CAS' in r.text:
        cas_sec = get_depth('CAS', id_sections)
        json_output['CAS-NUMBER'] = result_data['Record']['Section'][names_and_id]['Section'][other_id]['Section'][cas_sec]['Information'][0]['StringValue']
    else:
        json_output['CAS-NUMBER'] = ''
    if 'UN Number' in r.text:
        un_sec = get_depth('UN Number', id_sections)
        json_output['un-number'] = result_data['Record']['Section'][names_and_id]['Section'][other_id]['Section'][un_sec]['Information'][0]['StringValue']
    else:
        json_output['UN Number'] = ''
    if 'MeSH Synonyms' in r.text:
        mesh_sec = get_depth('MeSH Synonyms', syn_sections)
        json_output['MeSH synonyms'] = result_data['Record']['Section'][names_and_id]['Section'][synonyms]['Section'][mesh_sec]['Information'][0]['StringValueList']
    else:
        json_output['MeSH Synonyms'] = ''

    sections = result_data['Record']['Section'][chem_phys_props]['Section']
    computed_prop_dep = get_depth('Computed Properties', sections)
    comp_prop_sec = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section']
    exp_prop_dep = get_depth('Experimental Properties', sections)

    if 'Molecular Weight' in r.text:
        mol_weight = get_depth('Molecular Weight', comp_prop_sec)
        json_output['molecular-weight'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][mol_weight]['Information'][0]['NumValue']
    else:
        json_output['Molecular Weight'] = ''
    if 'Hydrogen Bond Donor Count' in r.text:
        hy_bond = get_depth('Hydrogen Bond Donor Count', comp_prop_sec)
        json_output['Hyrogen Bond Donor Count'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][hy_bond]['Information'][0]['NumValue']
    else:
        json_output['Hydrogen Bond Donor Count'] = ''
    if 'Hydrogen Bond Acceptor Count' in r.text:
        hy_bond_a = get_depth('Hydrogen Bond Acceptor Count', comp_prop_sec)
        json_output['Hyrogen Bond Acceptor Count'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][hy_bond_a]['Information'][0]['NumValue']
    else:
        json_output['Hydrogen Bond Acceptor Count'] = ''
    # if 'Rotatable Bond Count' in r.text:
    #     json_output['Rotatable Bond Count'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][chem_phys_props]['Information'][0]['NumValue']
    # else:
    #     json_output['Rotatable Bond Count'] = ''
    # if 'Exact Mass' in r.text:
    #     json_output['Exact Mass'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][5]['Information'][0]['NumValue']
    # else:
    #     json_output['Exact Mass'] = ''
    # if 'Heavy Atom Count' in r.text:
    #     json_output['Heavy Atom Count'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][8]['Information'][0]['NumValue']
    # else:
    #     json_output['Heavy Atom Count'] = ''
    # if 'Formal Charge' in r.text:
    #     json_output['Formal Charge'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][9]['Information'][0]['NumValue']
    # else:
    #     json_output['Formal Charge'] = ''
    # if 'Complexity' in r.text:
    #     json_output['Complexity'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][10]['Information'][0]['NumValue']
    # else:
    #     json_output['Complexity'] = ''
    # if 'Covalently-Bonded Unit Count' in r.text:
    #     json_output['Covalently-Bonded Unit Count'] = result_data['Record']['Section'][chem_phys_props]['Section'][computed_prop_dep]['Section'][16]['Information'][0]['NumValue']
    # else:
    #     json_output['Covalently-Bonded Unit Count'] = ''

    # print json_output
    # return r.json()
    # return jsonify(**result_data)
    return jsonify(**json_output)
    # return soup.prettify()

def get_depth(search_value, x):
    temp = 0
    level = 0
    for section in x:
        level = level + 1
        for key, value in section.iteritems():
            if value == search_value:
                temp = level - 1
                print search_value, temp
                return temp

def getPubChemID(compound, res_num):
    url2get = base_ncbi + c_search_path + compound.lower()
    r = requests.get(url2get, headers=headers)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    cid = soup.findAll('dt', string='CID')
    cidnum = []
    for elem in soup(text=re.compile(r'CID:')):
        cidnum.append(elem.parent.next_sibling.string)
    print res_num
    return cidnum[res_num]

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
