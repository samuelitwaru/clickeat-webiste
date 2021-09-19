from flask import Flask, request
from app import config


app = Flask(__name__)

app.config.from_object(config.ProductionConfig)
app.config.from_object(config.DevelopmentConfig)

# load context processsor
from app.context_processors import *

# load template filters
from app import template_filters


# load web app views
from app.views.index import index_bp
from app.views.product import product_bp


app.register_blueprint(index_bp)
app.register_blueprint(product_bp)