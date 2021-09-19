from flask import Blueprint, render_template, redirect, flash, url_for, request


product_bp = Blueprint('product', __name__, url_prefix='/product')


class Product:
	name = "Beef Burger - Town Grill"
	preprice = "UGX 22,000"
	price = "UGX 16,000"


@product_bp.route('')
def get_products():
	# code to get /search products
	return {}


@product_bp.route('<int:product_id>')
def get_product(product_id):
	# code to get product
	product = Product()
	return render_template('product/product.html', product=product)