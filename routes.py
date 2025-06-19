from flask import Blueprint, render_template, redirect, request, url_for, flash, abort, session
from flask_login import login_user, current_user,login_required,logout_user
from flask_mail import Message
from models import db, User
from forms import LoginForm, SignupForm,ForgotPasswordForm, ResetPasswordForm
from werkzeug.security import generate_password_hash, check_password_hash
from utils import generate_reset_token, verify_reset_token
from extensions import mail,redis_client
import re
from contributions import save_or_update_electricity_data, reset_electricity_data
from process_excel import process_excel, is_empty_or_nan, get_20_min_response_recommendations
import os
from process_excel import clear_redis_data
from flask import make_response


def slugify(name):
    return re.sub(r'[^a-zA-Z0-9\-]', '', name.replace(' ', '-')).lower()

app_routes = Blueprint('app_routes', __name__)

@app_routes.route('/')
def home():
    return render_template('index.html')

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            username_slug = slugify(user.fullname)
            return redirect(url_for('app_routes.dashboard', username=username_slug))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('app_routes.login'))
    return render_template('login.html', form=form)


@app_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists.', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(fullname=form.fullname.data, email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('app_routes.login'))
    return render_template('signup.html', form=form)

@app_routes.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(email)
            reset_url = url_for('app_routes.reset_password', token=token, _external=True)
            msg = Message('Reset Your Password',
                          sender='pyxlated.me@gmail.com',
                          recipients=[email])
            msg.body = f'Reset your password using this link: {reset_url}'
            mail.send(msg)
            flash('Password reset link sent to your email.', 'info')
            return redirect(url_for('app_routes.login'))
        else:
            flash('No account with that email.', 'warning')
            return redirect(url_for('app_routes.forgot_password'))  
    return render_template('forgot_password.html', form=form)

@app_routes.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('app_routes.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(form.password.data)
            db.session.commit() # Don't forget to commit the changes to the database
            flash('Your password has been changed successfully! Please log in.', 'success') 
            return redirect(url_for('app_routes.login'))
        else:
            flash('Error: User not found.', 'danger')
            return redirect(url_for('app_routes.forgot_password')) # Redirect back or to an error page
    else:
        # This block will execute if form validation fails (e.g., passwords don't match, or not strong enough)
        # The form.errors will contain messages from validators.
        # Your template (reset_password.html) should display form.errors for each field.
        pass # No explicit flash needed here, as template will show errors

    return render_template('reset_password.html', form=form, token=token) # Pass token to template for form action

@app_routes.route('/dashboard/<username>', methods=['GET', 'POST'])
@login_required
def dashboard(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    if not current_user.is_authenticated or not hasattr(current_user, 'fullname'):
        flash('Invalid user session.', 'danger')
        return redirect(url_for('app_routes.login'))
    # Check for percentage_contribution in Redis
    redis_key = f"electricity_data:user:{current_user.id}"
    contribution_data = redis_client.hgetall(redis_key)
    contribution_calculated = bool(contribution_data and contribution_data.get('percentage_contribution'))
    print("HELLO FROM DASHBOARD",flush=True)
    if request.method == 'POST':
        print("HELLO FROM DASHBOARD IN POST",flush=True)
        file = request.files.get('excel_file')
        print('File object:', file)

        if file:
            # Remove electricity data for this user before processing new file
            reset_electricity_data()
            print('File received:', file.filename)
            # Clear Redis before processing new file
            clear_redis_data(redis_client)
            # Save uploaded file to a known temp directory
            UPLOAD_DIR = '/tmp'  # Use /tmp for cloud platforms like Render
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            temp_path = os.path.join(UPLOAD_DIR, file.filename)
            file.save(temp_path)
            print(f"File saved at: {temp_path}, size: {os.path.getsize(temp_path)}")
            try:
                print("About to call process_excel", flush=True)
                process_excel(temp_path)
                print(f"Uploaded file: {file.filename}")
                num_keys = len(redis_client.keys('*'))
                print(f"Redis now contains {num_keys} keys after upload.")
                session['file_uploaded'] = True
                # flash('Excel file processed and data stored in Redis.', 'success')
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            print('No file received in POST request.')
            flash('No file uploaded.', 'danger')
    print("HELLO FROM DASHBOARD POST")
    return render_template('dashboard.html', user=current_user, contribution_calculated=contribution_calculated)


@app_routes.route('/dashboard/<username>/regionaloverview', methods=['GET', 'POST'])
@login_required
def regional_overview(username):

    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    percentage_contribution = None
    if request.method == 'POST':
        percentage_contribution = save_or_update_electricity_data(request.form)
    return render_template('regional_overview.html', user=current_user, percentage_contribution=percentage_contribution)


@app_routes.route('/dashboard/<username>/regionalgovernance', methods=['GET', 'POST'])
@login_required
def regional_governance(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    
    keys = redis_client.keys('sheet:GOVERNANCE:*')
    governance_data = []
    
    for key in keys:
        row = redis_client.hgetall(key)
        qn_no = row.get('qn_no', '')
        
        if qn_no.startswith('G'):
            indicator = row.get('indicator', '')
            subindicator = row.get('subindicator', '')
            
            # Clean up indicator and subindicator
            if is_empty_or_nan(indicator):
                indicator = ''
            if is_empty_or_nan(subindicator):
                subindicator = ''
                
            # Get response value and ensure it's properly rounded
            response_value = row.get('response_value', '')
            if response_value and response_value != '':
                try:
                    response_value = round(float(response_value), 2)
                except (ValueError, TypeError):
                    pass
            
            governance_data.append({
                'indicator': indicator,
                'subindicator': subindicator,
                'response_value': response_value,
                'qn_no': qn_no
            })
    
    # Sort by qn_no (natural order)
    def qn_sort_key(row):
        match = re.match(r'G\.Q(\d+)', row['qn_no'])
        return int(match.group(1)) if match else 0
    
    governance_data.sort(key=qn_sort_key)
    return render_template('regional_governance.html', user=current_user, governance_data=governance_data)


@app_routes.route('/dashboard/<username>/regionalmarketconditions', methods=['GET', 'POST'])
@login_required
def regional_market(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    keys = redis_client.keys('sheet:MARKET CONDITIONS:*')
    market_data = []
    for key in keys:
        row = redis_client.hgetall(key)
        qn_no = row.get('qn_no', '')
        if qn_no.startswith('M'):
            indicator = row.get('indicator', '')
            subindicator = row.get('subindicator', '')
            if is_empty_or_nan(indicator):
                indicator = ''
            if is_empty_or_nan(subindicator):
                subindicator = ''
            response_value = row.get('response_value', '')
            if response_value and response_value != '':
                try:
                    response_value = round(float(response_value), 2)
                except (ValueError, TypeError):
                    pass
            market_data.append({
                'indicator': indicator,
                'subindicator': subindicator,
                'response_value': response_value,
                'qn_no': qn_no
            })
    def qn_sort_key(row):
        match = re.match(r'M\.Q(\d+)', row['qn_no'])
        return int(match.group(1)) if match else 0
    market_data.sort(key=qn_sort_key)
    return render_template('regional_market.html', user=current_user, market_data=market_data)

@app_routes.route('/dashboard/<username>/consumerperception', methods=['GET', 'POST'])
@login_required
def consumer_perception(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    sheets = ['NON-PROSUMERS', 'LIVE-PROSUMERS']
    perception_data = []
    for sheet in sheets:
        keys = redis_client.keys(f'sheet:{sheet}:*')
        for key in keys:
            row = redis_client.hgetall(key)
            qn_no = row.get('qn_no', '')
            if qn_no.startswith('C'):
                indicator = row.get('indicator', '')
                subindicator = row.get('subindicator', '')
                if is_empty_or_nan(indicator):
                    indicator = ''
                if is_empty_or_nan(subindicator):
                    subindicator = ''
                response_value = row.get('response_value', '')
                if response_value and response_value != '':
                    try:
                        response_value = round(float(response_value), 2)
                    except (ValueError, TypeError):
                        pass
                perception_data.append({
                    'indicator': indicator,
                    'subindicator': subindicator,
                    'response_value': response_value,
                    'qn_no': qn_no
                })
    def qn_sort_key(row):
        match = re.match(r'C\.Q(\d+)', row['qn_no'])
        return int(match.group(1)) if match else 0
    perception_data.sort(key=qn_sort_key)
    return render_template('consumer_perception.html', user=current_user, perception_data=perception_data)

@app_routes.route('/dashboard/<username>/summary', methods=['GET', 'POST'])
@login_required
def summary(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    # Get summary values
    summary_values = redis_client.hgetall('summary_values')
    # Get user contribution data
    contribution_data = redis_client.hgetall(f"electricity_data:user:{current_user.id}")
    # Prepare values for template (convert to float or None)
    def safe_float(val):
        try:
            return float(val)
        except Exception:
            return None
    re_rmi_value = safe_float(contribution_data.get('re_rmi_value'))
    governance_maturity_index = safe_float(summary_values.get('governance_maturity_index'))
    market_maturity_index = safe_float(summary_values.get('market_maturity_index'))
    consumer_maturity_index = safe_float(summary_values.get('consumer_maturity_index'))
    # Get general recommendations (not from redis, but from Excel via helper)
    general_recommendations = get_20_min_response_recommendations()[:10]
    return render_template(
        're-rmi-summary.html',
        user=current_user,
        re_rmi_value=re_rmi_value,
        governance_maturity_index=governance_maturity_index,
        market_maturity_index=market_maturity_index,
        consumer_maturity_index=consumer_maturity_index,
        contribution_data=contribution_data, # <-- ensure this is passed
        general_recommendations=general_recommendations
    )

@app_routes.route('/dashboard/<username>/generate_report')
@login_required
def generate_report(username):
    expected_slug = slugify(current_user.fullname)
    if username != expected_slug:
        abort(403)
    contributions = redis_client.hgetall(f"electricity_data:user:{current_user.id}")
    summary_values = redis_client.hgetall('summary_values')
    re_rmi_value = float(contributions.get('re_rmi_value', 0)) if contributions.get('re_rmi_value') else None
    governance_maturity_index = float(summary_values.get('governance_maturity_index', 0)) if summary_values.get('governance_maturity_index') else None
    market_maturity_index = float(summary_values.get('market_maturity_index', 0)) if summary_values.get('market_maturity_index') else None
    consumer_maturity_index = float(summary_values.get('consumer_maturity_index', 0)) if summary_values.get('consumer_maturity_index') else None
    general_recommendations = get_20_min_response_recommendations()
    # Governance data
    keys = redis_client.keys('sheet:GOVERNANCE:*')
    governance_data = []
    for key in keys:
        row = redis_client.hgetall(key)
        qn_no = row.get('qn_no', '')
        if qn_no.startswith('G'):
            indicator = row.get('indicator', '')
            subindicator = row.get('subindicator', '')
            response_value = row.get('response_value', '')
            governance_data.append({
                'indicator': indicator,
                'subindicator': subindicator,
                'response_value': response_value,
                'qn_no': qn_no
            })
    # Market data
    keys = redis_client.keys('sheet:MARKET CONDITIONS:*')
    market_data = []
    for key in keys:
        row = redis_client.hgetall(key)
        qn_no = row.get('qn_no', '')
        if qn_no.startswith('M'):
            indicator = row.get('indicator', '')
            subindicator = row.get('subindicator', '')
            response_value = row.get('response_value', '')
            market_data.append({
                'indicator': indicator,
                'subindicator': subindicator,
                'response_value': response_value,
                'qn_no': qn_no
            })
    # Perception data
    sheets = ['NON-PROSUMERS', 'LIVE-PROSUMERS']
    perception_data = []
    for sheet in sheets:
        keys = redis_client.keys(f'sheet:{sheet}:*')
        for key in keys:
            row = redis_client.hgetall(key)
            qn_no = row.get('qn_no', '')
            if qn_no.startswith('C'):
                indicator = row.get('indicator', '')
                subindicator = row.get('subindicator', '')
                response_value = row.get('response_value', '')
                perception_data.append({
                    'indicator': indicator,
                    'subindicator': subindicator,
                    'response_value': response_value,
                    'qn_no': qn_no
                })
    return render_template(
        'pdf.html',
        preview_mode=True,
        contributions=contributions,
        re_rmi_value=re_rmi_value,
        governance_maturity_index=governance_maturity_index,
        market_maturity_index=market_maturity_index,
        consumer_maturity_index=consumer_maturity_index,
        general_recommendations=general_recommendations,
        governance_data=governance_data,
        market_data=market_data,
        perception_data=perception_data
    )

@app_routes.route('/logout')
def logout():
    # Use the unified clear_redis_data function for full cleanup
    clear_redis_data(redis_client)
    print("LOGOUT", flush=True)
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('app_routes.login'))