import os
import re
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

df = pd.read_csv(os.path.join(base_dir, 'data', 'houses.csv'))
model = joblib.load(os.path.join(base_dir, 'models', 'model.joblib'))
metrics_df = pd.read_csv(os.path.join(base_dir, 'models', 'metrics.csv'))
model_rmse = metrics_df['test_rmse']

with open('data/portugal.json') as f:
    pt_data = json.load(f)

districts_dict = {}
counties_dict = {}
for district in pt_data:
    counties = [county['name'] for county in district['conselhos']]
    districts_dict[district['name']] = counties
    for conselho in district['conselhos']:
        parishes = [parish['name'] for parish in conselho['freguesias']]
        counties_dict[conselho['name']] = parishes

label_encoder = LabelEncoder()
scaler = StandardScaler()


def predict_price(input_data) -> float:
    input_data = pd.DataFrame(input_data, index=[0])
    input_data['built_area'] = np.log(input_data['built_area'])

    objects = ['district', 'county', 'parish']
    for col in objects:
        input_data[col] = input_data[col].astype('category')
        label_encoder = joblib.load(os.path.join(
            base_dir, 'models', 'encoder_' + col + '.joblib'))
        input_data[col] = label_encoder.transform(input_data[col])

    input_data = input_data.astype('float32')

    numerical_cols = ['built_area', 'rooms', 'bathrooms']
    for col in numerical_cols:
        scaler = joblib.load(os.path.join(base_dir, 'models', 'scaler_' + col + '.joblib'))
        input_data[col] = scaler.transform(input_data[col].values.reshape(-1, 1))

    prediction = model.predict(input_data.values)
    prediction = np.exp(prediction[0])

    return prediction


@app.route("/")
def main():
    # JSX {% for item in data %} {{item.name}}
    data = {
        'districts': list(districts_dict.keys()),
    }
    return render_template('index.html', data=data)


@app.route('/select_county', methods=['POST'])
def select_county():
    data = request.form
    html = ''
    for entry in districts_dict[data['district']]:
        html += f'<option value="{entry}">{entry}</option>'.format(entry)
    return html


@app.route('/select_parish', methods=['POST'])
def select_parish():
    data = request.form
    html = ''
    for entry in counties_dict[data['county']]:
        label = entry
        if entry.startswith('União das freguesias de'):
            label = entry.replace('União das freguesias de ', '')
        html += f'<option value="{entry}">{label}</option>'.format(entry)
    return html


@app.route("/predict", methods=['POST'])
def predict():
    data = {
        'district': request.form['district'],
        'county': request.form['county'],
        'parish': request.form['parish'],
        'built_area': float(request.form['built_area']),
        'rooms': request.form['rooms'],
        'bathrooms': request.form['bathrooms'],
        'fitted_wardrobes': request.form['fitted_wardrobes'] == 'true',
        'air_conditioning': request.form['air_conditioning'] == 'true',
        'terrace': request.form['terrace'] == 'true',
        'balcony': request.form['balcony'] == 'true',
        'storeroom': request.form['storeroom'] == 'true',
        'with_lift': request.form['with_lift'] == 'true',
        'swimming_pool': request.form['swimming_pool'] == 'true',
        'garden': request.form['garden'] == 'true',
        'green_area': request.form['green_area'] == 'true',
        'is_apartment': request.form['is_apartment'] == 'true',
    }
    try:
        prediction = predict_price(data)

        rmse_low = prediction - model_rmse
        rmse_high = prediction + model_rmse

        rmse_low = f'{int(rmse_low):,}€'.replace(',', ' ')
        rmse_high = f'{int(rmse_high):,}€'.replace(',', ' ')

        return jsonify({
            'prediction': f'{int(prediction):,}€'.replace(',', ' '),
            'rmse_low': rmse_low,
            'rmse_high': rmse_high,
        })
    except Exception as e:
        label = re.findall(r"\'(.*?)\'", str(e))
        return jsonify({
            'error': label,
            'prediction': '0€',
            'rmse_low': '0€',
            'rmse_high': '0€',
            })


if __name__ == "__main__":
    # FLASK_APP=src/app.py FLASK_ENV=development flask run --port 8085
    app.run(host="0.0.0.0", port=8080, debug=True)
