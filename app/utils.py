import urllib
import uuid
from PIL import Image
import os
import json
from datetime import date, datetime, timedelta
from werkzeug.security import check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import url_for
from app.models import User, Profile, Role, Token, TimeSheet, WorkPerformance
from app.helpers import TimeSheetActionNotification, UserActivationNotification, Notification
import pytz
from app import app, db
from app.data import time_sheet_statuses
from app.template_filters  import is_weekend
import xlsxwriter


timezone = pytz.timezone(app.config.get("TIMEZONE"))


def authenticate_user(username, password):
	user = User.query.filter_by(username=username).first()
	if user and user.password and check_password_hash(user.password, password):
		return user
	return None


def current_time_sheet(user):
    # get the current user's timesheet i.e, a timesheet that is not yet approved
	time_sheet = TimeSheet.query.filter_by(approved=False, user=user).first()
	if time_sheet:
		return time_sheet
	
	current_date = datetime.now()
	month = current_date.month; year = current_date.year
	current_month = datetime(year, month, 1)
	time_sheet = TimeSheet.query.filter_by(month=current_month, user=user).first()
	return time_sheet


def join_telephone(code, telephone, joiner="-"):
	return f"{code}{joiner}{telephone}"


def split_telephone(telephone, splitter="-"):
	return telephone.split(splitter)


def assign_user_roles(user, roles):
	roles_instances = Role.query.filter(Role.name.in_(roles))
	user.roles.extend(roles_instances)
	return user.roles

def remove_user_roles(user, roles):
	roles_instances = Role.query.filter(Role.name.in_(roles))
	for role in roles_instances:
		user.roles.remove(role)
	return user.roles


def create_xlsx_template(fields, template_filename='template.xlsx'):
	"""
	[{'name':'name', validation:{}}]
	"""
	letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	workbook = xlsxwriter.Workbook(f'{app.config.get("MEDIA_URL")}/generated/{template_filename}')
	worksheet = workbook.add_worksheet("main")
	bold = workbook.add_format({'bold': True})
	col=0
	row=0
	for field in fields:
		field_name = field.get("name", "Unnamed")
		worksheet.write(row, col, field_name, bold)
		worksheet.data_validation(f'{letters[col]}1', {"validate":"custom", "value": f'=${field_name}'})
		worksheet.data_validation(f'{letters[col]}2:{letters[col]}1048576', validate_xlsx_column(field.get("validate", {}), workbook))
		worksheet.set_column(col, 0, len(field_name)*3)
		data = field.get("data")
		if data:
			worksheet.write_column(1, col, data, bold)
		col += 1
	row += 1

	workbook.close()
	return template_filename


def validate_xlsx_column(validation_dict, workbook):
	if validation_dict.get('validate') == 'list' and len(str(validation_dict.get('source'))) > 255:
		row = 0
		col = 0
		worksheet_name = gen_random_string(10)
		worksheet = workbook.add_worksheet(worksheet_name)
		for item in validation_dict.get('source'):
			worksheet.write(row, col, item)
			row += 1
		validation_dict["source"] = f"={worksheet_name}!$A$1:$A${row}"

	return validation_dict


def generate_month_dates(month, year):
	last_day = get_last_day_of_the_month(month, year)
	ndays = (last_day - datetime(year, month, 1)).days + 1
	d1 = datetime(year, month, 1)
	d2 = datetime(year, month, ndays)
	delta = d2 - d1
	return [(d1 + timedelta(days=i)) for i in range(delta.days + 1)]


def get_last_day_of_the_month(month, year):
	if month == 12:
		next_month = 1
		next_year = year + 1
	else:
		next_month = month + 1
		next_year = year

	return datetime(next_year, next_month, 1) - timedelta(1)


def date_cell_format(data_row):
	cell_format = {'num_format': 'ddd, dd/mm'}
	date, _, _, _ = data_row
	if is_weekend(date):
		cell_format["bg_color"] = "#FFC000"
	return cell_format

	
def get_super_user(role_name, branch_id=0):
	def filter_user(user):
		return role_name in user.get_roles()
	user_query = User.query
	if branch_id:
		user_query = user_query.filter_by(branch_id=branch_id)
	filtered = filter(filter_user, user_query)
	for user in filtered:
		return user

def get_users_in_branch(branch):
	return [member.user for member in branch.members]


def get_users_with_role(role_name, only_non_super=False):
	def filter_user(user):
		roles = user.get_roles()
		if only_non_super:
			return not user.is_super() and (role_name in roles)
		return role_name in roles
	filtered = filter(filter_user, User.query.all())
	users = []
	for user in filtered:
		users.append(user)
	return users


def get_branch_users_with_role(branch, role_name, only_non_super=False):
	def filter_branch_users(user):
		roles = user.get_roles()
		if only_non_super:
			return not user.is_super() and (role_name in roles)
		return role_name in roles
	
	filtered = filter(filter_branch_users, branch.users.all())
	users = []
	for user in filtered:
		users.append(user)
	return users


def create_user_token(user, token_period=3600):
	s = Serializer(app.config['SECRET_KEY'], expires_in=token_period)
	token = s.dumps({ 'confirm': 23 }).decode()
	expiry = datetime.now() + timedelta(seconds=token_period)
	token = Token(token=token, expiry=expiry)
	token.user = user
	db.session.add(token)


def generate_notifications(user, generate_link=True):
	roles = user.get_roles()
	notifications = []
	# get time sheets that {user} is in charge
	time_sheets = TimeSheet.query.filter_by(user_in_charge=user).all()
	# for each time_sheet
	for time_sheet in time_sheets:
		notification = TimeSheetActionNotification(time_sheet, generate_link=generate_link)
		if notification.subject:
			notifications.append(notification)
	if "admin" in roles:
		# generate request for late submission notifications
		def filter_time_sheet(time_sheet):
			latest_action = time_sheet.latest_action()
			if latest_action and latest_action.action=='late_submission_request':
				return True
		filtered = filter(filter_time_sheet, user.branch.get_time_sheets().all()) 
		for each in filtered:
			notification = Notification(
					subject="Request for late submission",
					description="",
					link=url_for('time_sheet.get_time_sheet', time_sheet_id=each.id),
					associated_user=each.user
				)
			notifications.append(notification)


		inactive_users = User.query.filter_by(is_active=False, branch_id=user.branch_id).all()
		if inactive_users:
			notification = UserActivationNotification(inactive_users, generate_link=generate_link)
			notifications.append(notification)
	return notifications


def filter_time_sheets(month_gte=None, month_lte=None, user_id=0, status=0):
	def filter_by_status(time_sheet):
		print(time_sheet_statuses.get(status) == time_sheet.status())
		return time_sheet_statuses.get(status) == time_sheet.status()
	query = TimeSheet.query
	if month_gte:
	    query = query.filter(TimeSheet.month>=month_gte)
	if month_lte:
	    query = query.filter(TimeSheet.month<=month_lte)
	if user_id:
		query = query.filter_by(user_id=user_id)

	if status:
		time_sheet_ids = [time_sheet.id for time_sheet in filter(filter_by_status, query.all())]
		query = query.filter(TimeSheet.id.in_(time_sheet_ids))

	return query


def crop_image(image_path, crop_path, x,y,w,h, size=None):
	im = Image.open(image_path)
	im1 = im.crop((x, y, x+w, y+h))
	if size: im1 = im1.resize(size=size)
	im1.save(crop_path)


def save_signature(profile_id, signature, x, y, w, h):
	# give image a name
	split = signature.filename.split('.')
	ext = split[-1]
	filename = f"{profile_id}.{ext}"

	sign_filepath = f"{app.config['UPLOAD_DIR']}/signatures/{filename}"
	temp_filepath = f"{app.config['TMP_DIR']}/tmp_{filename}"

	signature.save(temp_filepath)
	
	crop_image(temp_filepath, sign_filepath, x, y, w, h, (200,90))
	
	os.remove(temp_filepath)
	
	return filename


def parse_query_string(query_string):
	result = urllib.parse.parse_qs(query_string)
	for k, v in result.items():
		if isinstance(v, list) and len(v) == 1:
			result[k] = v[0]
	return result


def parse_json_string(json_string):
	return json.loads(json_string)


def create_blank_time_sheet_work_performances(time_sheet):
	month_dates = generate_month_dates(time_sheet.month.month, time_sheet.month.year)
	for  date in month_dates:
		work_performance = WorkPerformance(date=date)
		db.session.add(work_performance)
		time_sheet.work_performances.append(work_performance)


def generate_time_sheet_signature_cells(time_sheet):
	signatures = []
	status = time_sheet.status()
	if status != "EDITING" and status!='REJECTED':
		profile = time_sheet.user.profile 
		signatures.append({"col": 1, "row": 53, "type": "STRING", "data": f"Date, Signature of Expert ({profile})", "format": {"top": True}},)
		signatures.append({"col": 1, "row": 54, "type": "IMAGE", "data": f"app/media/uploads/signatures/{profile.signature}"})
	else:
		signatures.append({"col": 1, "row": 54, "type": "STRING", "data": f""})

	if time_sheet.approved:
		admin = get_super_user("admin", time_sheet.user.branch_id)
		admin_profile = admin.profile
		signatures.append({"col": 1, "row": 59, "type": "STRING", "data": f"Date, Signature of Team Leader ({admin_profile})", "format": {"top": True}})
		signatures.append({"col": 1, "row": 60, "type": "IMAGE", "data": f"app/media/uploads/signatures/{admin_profile.signature}"})
	else:
		signatures.append({"col": 1, "row": 60, "type": "STRING", "data": f""})

	return signatures


def generate_timesheet_total_cell(len_month_dates, len_work_performances):
	return {
		"col": 2,
		"row": 48,
		"type": "LIST",
		"list": list(range(0, len_month_dates+1)),
		"data":len_work_performances,
		"format": {
		  "border": True
		}
	}