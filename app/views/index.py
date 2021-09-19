from flask import Blueprint, render_template, redirect, flash, url_for, request


index_bp = Blueprint('index', __name__, url_prefix='/')


@index_bp.route('/')
def index():
	return render_template("index/index.html")


@index_bp.route('/signin-signup')
def signin_signup():
	return render_template("signin_signup/signin-signup.html")