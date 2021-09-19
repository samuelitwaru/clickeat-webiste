from jinja2 import filters
from app import app
from datetime import datetime
from wtforms.validators import DataRequired
import re


def datetimeformat(value, format='%d/%m/%Y %H:%M'):
	if isinstance(value, datetime):
		return value.strftime(format)


def currency(value):
	if isinstance(value, int):
		return f'{value:,} {app.config.get("DEFAULT_CURRENCY", "")}'
	return value


def is_required(field):
	for validator in field.validators:
		if isinstance(validator, DataRequired):
			return True
	return False


def is_weekend(date):
	day = date.strftime("%a")
	if day == "Sun" or day == "Sat":
		return True
	return False


def get_filled_activity_count(activities):
	count = 0
	for activity in activities:
		if activity.is_filled():
			count += 1
	return count


def build_query_string(args):
	query_string = "?"
	for k, v in args.items():
		query_string += f"{k}={v}&"
	return query_string



filters.FILTERS['datetimeformat'] = datetimeformat
filters.FILTERS['currency'] = currency
filters.FILTERS['is_required'] = is_required
filters.FILTERS['is_weekend'] = is_weekend
filters.FILTERS['get_filled_activity_count'] = get_filled_activity_count
filters.FILTERS['build_query_string'] = build_query_string
