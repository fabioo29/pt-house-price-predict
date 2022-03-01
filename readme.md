<!-- PROJECT LOGO -->
<br />
<p align="center">

  <h3 align="center">Predicting house prices in Portugal</h3>

  <p align="center">
    Regression Based Problem :: Supervised Problem :: Machine learning algorithms 
    <br />
  </p>
  </br>
  <p align="center">
    <img src="images/interface.gif" alt="web app" width="570" height="300" />
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li><a href="#about">About</a></li>
    <li><a href="#testing">Testing</a></li>
    <li><a href="#contribution">Contribution</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About

<div style="text-align: justify">
  
**Motivation**: Academic project for Machine Learning Algorithms, M2AI. Choose a dataset to use Supervised Learning, Unsupervised Learning or Reinforcement Learning algorithms.

**Implementation**: All the code was implemented in python and it can be divided in three parts: **(1)** There's a web scrapper in src/scrapper.py that is responsible to extract all the houses currently available in one of the largest Portuguese houses market website. Each house has 22 features including the target feature (price). **(2)** There's a notebook in notebooks/house_price_eda.ipynb that is responsible for all the data exploration, data cleaning and data preparation. It also has the step where the model is trained from the filtered dataset. **(3)** There's a Flask python code which is responsible to open the web app and handle the requests from the user in order to ask the model for a prediction given the user house inputs as shown in the gif above.

**_Tested with_** Random Forest, XGBoost and CatBoost regression algorithms.

**_Built With_** Python3.6, sklearn and Flask.

<!-- SIMULATION -->

## Testing

```python
# install the requirements
pip install -r requirements.txt

# scrape the data
python src/scrapper.py

# create the regression based model
# run the notebooks/house_price_eda.ipynb notebook

# run the web app
FLASK_APP=src/app.py FLASK_ENV=development flask run --port 8085
```

## Contribution

Feel free to submit a pull request with your improvements for the web scraper/notebook.

## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- CONTACT -->

## Contact

Fábio Oliveira - [LinkedIn](https://www.linkedin.com/in/fabioo29/) - fabiodiogo29@gmail.com

Project Link: [https://github.com/fabioo29/pt-house-price-predict](https://github.com/fabioo29/pt-house-price-predict)  
Project built as a Msc. Applied Artificial Intelligence Student.
