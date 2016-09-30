#!/usr/bin/python
import requests,re,sys,json,os.path
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

base_pub = 'https://pubchem.ncbi.nlm.nih.gov/compound/'
base_pub2 = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'
base_ncbi = 'https://www.ncbi.nlm.nih.gov/'
c_search_path = 'pccompound?term='
headers = {'user-agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; \
rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'}
no_results = []
retry_search = []
json_errors = []

# takes a string "[group id] [compound]"
def json_output(x):
    if len(sys.argv) == 3:
        req_num = int(sys.argv[2])
    else:
        req_num = 0
    req_compound = x.split(' ',1)[1]
    group_id = x.split()[0]
    # print group_id, req_compound

    cid = getPubChemID(req_compound, req_num)
    if cid == -1:
        no_results.append(x)
        return -1
    url2get = base_pub2 + cid + '/JSON/'
    # print url2get
    r = requests.get(url2get, headers=headers)
    html = r.text
    soup = BeautifulSoup(html, "html5lib")
    try:
        result_data = json.loads(r.content)
    except UnicodeDecodeError:
        json_errors.append(x)
        return -1
    json_output = {}


    try:
        sections = result_data['Record']['Section']
        names_and_id = get_depth('Names and Identifiers', sections)
        chem_phys_props = get_depth('Chemical and Physical Properties', sections)
        sections = result_data['Record']['Section'][names_and_id]['Section']
        record_title = get_depth('Record Title', sections)
        computed_desc = get_depth('Computed Descriptors', sections)
        other_id = get_depth('Other Identifiers', sections)
        id_sections = result_data['Record']['Section'][names_and_id]['Section']\
                [other_id]['Section']
        synonyms = get_depth('Synonyms', sections)
        syn_sections = result_data['Record']['Section'][names_and_id]['Section']\
                [synonyms]['Section']

        computed_sections = result_data['Record']['Section'][names_and_id]\
                ['Section'][computed_desc]['Section']

        comp_sections = result_data['Record']['Section'][chem_phys_props]['Section']
        computed_prop_dep = get_depth('Computed Properties', comp_sections)
        comp_prop_sec = result_data['Record']['Section'][chem_phys_props]\
                ['Section'][computed_prop_dep]['Section']
        exp_prop_dep = get_depth('Experimental Properties', comp_sections)

        # CAS-NUMBER
        if re.search('\"CAS\"',r.text):
            cas_sec = get_depth('CAS', id_sections)
            json_output['CAS-NUMBER'] = result_data['Record']['Section']\
                    [names_and_id]['Section'][other_id]['Section'][cas_sec]\
                    ['Information'][0]['StringValue']
        else:
            json_output['CAS-NUMBER'] = ''

        # PubChem ID
        json_output['PubChecm ID'] = result_data['Record']['RecordNumber']

        # Canonical SMILES
        if re.search('\"Canonical SMILES\"',r.text):
            c_smiles_sec = get_depth('Canonical SMILES', computed_sections)
            json_output.setdefault('Canonical SMILES',[]).append(
                    result_data['Record']['Section'][names_and_id]['Section']\
                            [computed_desc]['Section'][c_smiles_sec]['Information']\
                            [0]['StringValue'])
        else:
            json_output['Canonical SMILES'] = []

        # Isomeric SMILES
        if re.search('\"Isomeric SMILES\"',r.text):
            i_smiles_sec = get_depth('Isomeric SMILES', computed_sections)
            json_output.setdefault('Isomeric SMILES',[]).append(
                    result_data['Record']['Section'][names_and_id]['Section']\
                            [computed_desc]['Section'][i_smiles_sec]['Information']\
                            [0]['StringValue'])
        else:
            json_output['Isomeric SMILES'] = []

        # name
        json_output['name'] = result_data['Record']['Section'][names_and_id]\
                ['Section'][record_title]['Information'][0]['StringValue']

        # un-number
        if re.search('\"UN Number\"',r.text):
            un_sec = get_depth('UN Number', id_sections)
            json_output.setdefault('un-number',[]).append(result_data['Record']\
                    ['Section'][names_and_id]['Section'][other_id]['Section']\
                    [un_sec]['Information'][0]['StringValue'])
        else:
            json_output['UN Number'] = []

        # InChI-key
        if re.search('\"InChI Key\"',r.text):
            inchi_key_sec = get_depth('InChI Key', computed_sections)
            json_output['InChI-key'] = result_data['Record']['Section']\
                    [names_and_id]['Section'][computed_desc]['Section']\
                    [inchi_key_sec]['Information'][0]['StringValue']
        else:
            json_output['InChI-key'] = ''

        # molecular-formula
        if re.search('\"Molecular Formula\"',r.text):
            molecular_form = get_depth('Molecular Formula', sections)
            json_output.setdefault('molecular-formula',[]).append(
                    result_data['Record']['Section'][names_and_id]['Section']\
                            [molecular_form]['Information'][0]['StringValue'])
        else:
            json_output['molecular-formula'] = []

        # molecular-weight
        if re.search('\"Molecular Weight\"',r.text):
            mol_weight = get_depth('Molecular Weight', comp_prop_sec)
            json_output['molecular-weight'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [mol_weight]['Information'][0]['NumValue']
        else:
            json_output['Molecular Weight'] = ''

        # MeSH synonyms
        if re.search('\"MeSH Synonyms\"',r.text):
            mesh_sec = get_depth('MeSH Synonyms', syn_sections)
            json_output['MeSH synonyms'] = result_data['Record']['Section']\
                    [names_and_id]['Section'][synonyms]['Section'][mesh_sec]\
                    ['Information'][0]['StringValueList']
        else:
            json_output['MeSH Synonyms'] = []

        # Hydrogen Bond Donor Count
        if re.search('\"Hydrogen Bond Donor Count\"',r.text):
            hy_bond = get_depth('Hydrogen Bond Donor Count', comp_prop_sec)
            json_output['Hyrogen Bond Donor Count'] = result_data['Record']\
                    ['Section'][chem_phys_props]['Section'][computed_prop_dep]\
                    ['Section'][hy_bond]['Information'][0]['NumValue']
        else:
            json_output['Hydrogen Bond Donor Count'] = ''

        # Hydrogen Bond Acceptor Count
        if re.search('\"Hydrogen Bond Acceptor Count\"',r.text):
            hy_bond_a = get_depth('Hydrogen Bond Acceptor Count', comp_prop_sec)
            json_output['Hyrogen Bond Acceptor Count'] = result_data['Record']\
                    ['Section'][chem_phys_props]['Section'][computed_prop_dep]\
                    ['Section'][hy_bond_a]['Information'][0]['NumValue']
        else:
            json_output['Hydrogen Bond Acceptor Count'] = ''

        # Rotatable Bond Count
        if re.search('\"Rotatable Bond Count\"',r.text):
            r_bond_cnt = get_depth('Rotatable Bond Count', comp_prop_sec)
            json_output['Rotatable Bond Count'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [r_bond_cnt]['Information'][0]['NumValue']
        else:
            json_output['Rotatable Bond Count'] = ''

        # Exact Mass
        if re.search('\"Exact Mass\"',r.text):
            e_mass = get_depth('Exact Mass', comp_prop_sec)
            json_output['Exact Mass'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [e_mass]['Information'][0]['NumValue']
        else:
            json_output['Exact Mass'] = ''

        # Heavy Atom Count
        if re.search('\"Heavy Atom Count\"',r.text):
            h_atom_cnt = get_depth('Heavy Atom Count', comp_prop_sec)
            json_output['Heavy Atom Count'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [h_atom_cnt]['Information'][0]['NumValue']
        else:
            json_output['Heavy Atom Count'] = ''

        # Formal Charge
        if re.search('\"Formal Charge\"',r.text):
            f_charge = get_depth('Formal Charge', comp_prop_sec)
            json_output['Formal Charge'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [f_charge]['Information'][0]['NumValue']
        else:
            json_output['Formal Charge'] = ''

        # Complexity
        if re.search('\"Complexity\"',r.text):
            complexity = get_depth('Complexity', comp_prop_sec)
            json_output['Complexity'] = result_data['Record']['Section']\
                    [chem_phys_props]['Section'][computed_prop_dep]['Section']\
                    [complexity]['Information'][0]['NumValue']
        else:
            json_output['Complexity'] = ''

        # Covalently-Bonded Unit Count
        if re.search('\"Covalently-Bonded Unit Count\"',r.text):
            c_bond_unit = get_depth('Covalently-Bonded Unit Count', comp_prop_sec)
            json_output['Covalently-Bonded Unit Count'] = result_data['Record']\
                    ['Section'][chem_phys_props]['Section'][computed_prop_dep]\
                    ['Section'][c_bond_unit]['Information'][0]['NumValue']
        else:
            json_output['Covalently-Bonded Unit Count'] = ''

        json_output['Melting Point'] = []
        json_output['Boiling Point'] = []
        json_output['Freezing Point'] = []
        json_output['Chemical/Compound'] = 'compound'
        json_output['Reaction Group ID'] = int(group_id)
    except KeyError:
        retry_search.append(x)
        return -1

    return json_output

def get_depth(search_value, x):
    temp = 0
    level = 0
    for section in x:
        if temp > 0:
            break
        else:
            level = level + 1
            for key, value in section.iteritems():
                if temp > 0:
                    break
                else:
                    if value == search_value:
                        temp = level - 1
                    # print search_value, temp
    return int(temp)

def getPubChemID(compound, res_num):
    url2get = base_ncbi + c_search_path + compound.lower()
    r = requests.get(url2get, headers=headers)
    if len(r.history) < 1 or r.history[0].status_code != 303:
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        cid = soup.findAll('dt', string='CID')
        cidnum = []
        for elem in soup(text=re.compile(r'CID:')):
            cidnum.append(elem.parent.next_sibling.string)
        if len(cidnum) > 0:
            return cidnum[res_num]
        else:
            return -1
    else:
        return filter(str.isdigit, r.history[0].headers['Location'])

def loop_file(content):
    record_count = 0
    final_output = []
    for arg in content:
        output = json_output(arg)
        if output != -1:
            record_count += 1
            final_output.append(output)
    if len(final_output) > 0:
        with open('output.json', 'w') as file_output:
            file_output.write(
                json.dumps(final_output, sort_keys=True, indent=4, \
                        separators=(',',':'))
                        )
        print str(record_count) + ' records were created\n'
def report_errors():
    if len(json_errors) > 0:
        print 'There were decoding errors for the output of'
        for result in json_errors:
            print result
            with open('errors.log', 'a') as file_output:
                file_output.write(result)
    if len(retry_search) > 0:
        print 'Retry the following inputs'
        for result in retry_search:
            print result
            with open('retry.log', 'a') as file_output:
                file_output.write(result)
    if len(no_results) > 0:
        print 'No results found for'
        for result in no_results:
            print result
            with open('no_results.log', 'a') as file_output:
                file_output.write(result)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Try "python scrape.py [file]", where the file contains "' + \
                '[group_id] [compound]" delimited by a new line. (see example.txt)'
        exit()
    else:
        if os.path.isfile('output.json'):
            print 'output.json already exists, rename, move or delete the ' + \
                    'file and try again'
            exit()
        print 'This is going to take a while...'
        with open(sys.argv[1]) as f:
            content = f.readlines()
            loop_file(content)
            report_errors()
