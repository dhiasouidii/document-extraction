

from flask import Flask, request, flash, redirect
from flask_restful import Api
import re
import warnings
import re
import pandas as pd
import PyPDF2
from tabula import read_pdf
import json
import base64
import io

def extract_total(text):
    regex = r"Montant achat\s+(\d+(\.\d+)?)"
    match = re.search(regex, text)

    if match:
        number = match.group(1)
        return number


def extract_date_commande(text):
    regex = r"Date de commande (\d{2}/\d{2}/\d{4})"
    match = re.search(regex, text)
    if match:
        date = match.group(1)
        return date


def extract_date_livraison(text):
    regex = r"Date de livraison impérative (\d{2}/\d{2}/\d{4})"
    match = re.search(regex, text)
    if match:
        date = match.group(1)
        return date


def extract_lieu_livraison(text):
    lieu = re.findall(r'Facturation\n(.*)', text)[0]
    return lieu


def extract_destinataire(text):
    lieu = re.findall(r'(.*)Téléphone\nFax\nEmail\nSite(.*)', text)
    return lieu[-1][1]


ALLOWED_EXTENSIONS = {'txt'}
app = Flask(__name__)
api = Api(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file in request'
        
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No selected file'
        
        if not allowed_file(file.filename):
            return 'File extension not allowed'
        
        if file and allowed_file(file.filename):
            pages = []
            data = file.read()
            pdf_file = base64.b64decode(data)
            pdf_file = io.BytesIO(pdf_file)
        
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Get the total number of pages in the PDF document
            num_pages = len(pdf_reader.pages)
            output = []
            for i in range(num_pages):
                page = pdf_reader.pages[i]
                output.append(page.extract_text())
            output = ' '.join(output)

            col_boundaries = '--columns 10,20,30'
            tables = read_pdf(pdf_file, pages='all', lattice=False,
                              encoding='cp1252', options=col_boundaries)
            tables.pop(0)
            elements = pd.concat(tables)
            elements = elements.rename(columns={'Unnamed: 0': 'N° article',
                                                'Unnamed: 1': 'EAN principal',
                                                'Unnamed: 2': 'Libellé',
                                                'Unnamed: 3': 'Nb colis',
                                                'Unnamed: 4': 'PCB',
                                                'Unnamed: 5': 'Qté',
                                                'Unnamed: 6': 'Prix achat en DIN',
                                                'Montant': 'Montant promo DIN',
                                                'Unnamed: 7': 'TVA',
                                                })
            elements = elements[pd.to_numeric(
                elements['N° article'], errors='coerce').notnull()]
            elements = elements.reset_index()
            elements = elements.fillna(0)
            elements = elements.to_dict(orient='records')
            json_str = json.dumps(elements)

            # Loop through each page in the PDF document
            for page_num in range(num_pages):

                # Get the text from the current page
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                pages.append(text)

            return {'Destinataire': extract_destinataire(output),
                    'Lieu de Livraison': extract_lieu_livraison(output),
                    'Date de la Commande': extract_date_commande(output),
                    'Date de la Livraison': extract_date_livraison(output),
                    'Total': extract_total(output),
                    'Lignes': json.loads(json_str),
                    'Nombre des lignes': len(elements)}
    else:
        return 'Method not Allowed'


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(port=5000, debug=False)
