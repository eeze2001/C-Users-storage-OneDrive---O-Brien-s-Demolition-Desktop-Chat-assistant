"""
O'Brien's Storage Finder - Web Application
Copyright (c) 2025 John Hibberd
All rights reserved.
"""
import os
import sys
import importlib.util
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Import the storage finder logic
try:
    # Handle filename with space - use absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    storage_finder_path = os.path.join(current_dir, "Storage Finder.py")
    
    # Check if file exists
    if not os.path.exists(storage_finder_path):
        raise FileNotFoundError(f"Storage Finder.py not found at {storage_finder_path}")
    
    spec = importlib.util.spec_from_file_location("storage_finder", storage_finder_path)
    if spec is None or spec.loader is None:
        raise ImportError("Failed to create spec for Storage Finder.py")
    
    storage_finder = importlib.util.module_from_spec(spec)
    sys.modules["storage_finder"] = storage_finder
    spec.loader.exec_module(storage_finder)
    print("Successfully imported storage_finder module")
except Exception as e:
    import traceback
    error_msg = f"Error importing storage_finder: {e}\n{traceback.format_exc()}"
    print(error_msg)
    # Raise the error so we know what's wrong
    raise

# Static prices (only these are hardcoded)
STATIC_PRICES = {
    'container': {
        'deposit': 120,
        'lock': 25
    },
    'internal': {
        'deposit': 50,
        'padlock': 9.99
    }
}

# UK phone number validation
def validate_uk_phone(phone):
    """Validate UK phone number format"""
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    # UK phone patterns
    patterns = [
        r'^0\d{10}$',  # 01123456789
        r'^\+44\d{10}$',  # +441123456789
        r'^0044\d{10}$',  # 00441123456789
        r'^07\d{9}$',  # 07123456789 (mobile)
    ]
    return any(re.match(p, phone) for p in patterns)

# Email validation
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/start', methods=['GET', 'POST'])
def start():
    """Customer information form"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        errors = []
        if not name:
            errors.append('Name is required')
        if not phone:
            errors.append('Phone number is required')
        elif not validate_uk_phone(phone):
            errors.append('Please enter a valid UK phone number')
        if not email:
            errors.append('Email address is required')
        elif not validate_email(email):
            errors.append('Please enter a valid email address')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('start.html')
        
        # Store in session
        session['customer_name'] = name
        session['customer_phone'] = phone
        session['customer_email'] = email
        
        return redirect(url_for('find_storage'))
    
    return render_template('start.html')

@app.route('/find-storage')
def find_storage():
    """Main storage finding flow"""
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    return render_template('find_storage.html')

@app.route('/api/sites')
def api_sites():
    """Get available sites"""
    sites = [
        {'id': 'wallsend', 'name': 'Wallsend'},
        {'id': 'boldon', 'name': 'Boldon'},
        {'id': 'birtley', 'name': 'Birtley'},
        {'id': 'sunderland', 'name': 'Sunderland'},
        {'id': 'chester-le-street', 'name': 'Chester-le-Street'}
    ]
    return jsonify(sites)

@app.route('/items-input', methods=['GET', 'POST'])
def items_input():
    """Input items for size calculation"""
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash('Please describe what you want to store', 'error')
            return render_template('items_input.html')
        
        session['description'] = description
        # Need to choose storage type first, then site
        return redirect(url_for('choose_storage_type_for_items'))
    
    return render_template('items_input.html')

@app.route('/choose-storage-type-for-items', methods=['GET', 'POST'])
def choose_storage_type_for_items():
    """Choose storage type when coming from items input"""
    if 'customer_name' not in session or 'description' not in session:
        return redirect(url_for('items_input'))
    
    if request.method == 'POST':
        storage_type = request.form.get('storage_type')
        if storage_type in ['container', 'internal']:
            session['storage_type'] = storage_type
            
            # If internal storage, auto-select Sunderland and skip site selection
            if storage_type == 'internal':
                session['site'] = 'sunderland'
                return redirect(url_for('process_items'))
            else:
                # Container storage - need to choose site
                return redirect(url_for('select_site'))
        else:
            flash('Please select a storage type', 'error')
    
    return render_template('choose_size.html')

@app.route('/choose-size', methods=['GET', 'POST'])
def choose_size():
    """Choose a specific size"""
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    if request.method == 'POST':
        storage_type = request.form.get('storage_type')
        if not storage_type:
            flash('Please select a storage type', 'error')
            return render_template('choose_size.html')
        
        session['storage_type'] = storage_type
        session['size_method'] = 'known'
        
        # If internal storage, auto-select Sunderland and skip site selection
        if storage_type == 'internal':
            session['site'] = 'sunderland'
            return redirect(url_for('select_known_size'))
        else:
            # Container storage - need to choose site
            return redirect(url_for('select_site'))
    
    return render_template('choose_size.html')

@app.route('/select-site', methods=['GET', 'POST'])
def select_site():
    """Select storage site"""
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    # Get storage type from session (default to container if not set)
    storage_type = session.get('storage_type', 'container')
    
    if request.method == 'POST':
        site = request.form.get('site')
        if not site:
            flash('Please select a site', 'error')
            return render_template('select_site.html', storage_type=storage_type)
        
        # Validate site selection based on storage type
        if storage_type == 'internal' and site != 'sunderland':
            flash('Internal storage is only available at Sunderland', 'error')
            return render_template('select_site.html', storage_type=storage_type)
        
        session['site'] = site
        # Ensure storage_type is set (default to container)
        if 'storage_type' not in session:
            session['storage_type'] = 'container'
        
        # Process based on method
        if session.get('size_method') == 'known':
            return redirect(url_for('select_known_size'))
        else:
            # Calculate size from items
            return redirect(url_for('process_items'))
    
    return render_template('select_site.html', storage_type=storage_type)


@app.route('/process-items')
def process_items():
    """Process items and calculate size"""
    if storage_finder is None:
        flash('Application error: Storage finder module not loaded. Please contact support.', 'error')
        return redirect(url_for('index'))
    
    if 'customer_name' not in session or 'description' not in session:
        return redirect(url_for('items_input'))
    
    # Make sure we have storage type and site selected
    if 'storage_type' not in session:
        return redirect(url_for('choose_storage_type_for_items'))
    
    if 'site' not in session:
        return redirect(url_for('select_site'))
    
    description = session['description']
    storage_type = session.get('storage_type')
    
    # Use the storage_finder logic to analyze description
    items, _, vehicle_mentioned = storage_finder.analyze_initial_description(description)
    
    # Check for prohibited items
    prohibited = storage_finder.check_prohibited_items(items, storage_type)
    
    # Check for vehicle in internal storage
    if vehicle_mentioned and storage_type == 'internal':
        session['vehicle_warning'] = True
        return redirect(url_for('vehicle_warning'))
    
    # Calculate size
    size, unrecognized = storage_finder.calculate_size_from_items(items)
    session['calculated_size'] = size
    session['items'] = items
    session['unrecognized_items'] = unrecognized
    session['prohibited_items'] = prohibited
    
    return redirect(url_for('show_results'))

@app.route('/select-known-size', methods=['GET', 'POST'])
def select_known_size():
    """Select a known size"""
    if storage_finder is None:
        flash('Application error: Storage finder module not loaded. Please contact support.', 'error')
        return redirect(url_for('index'))
    
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    site = session.get('site')
    storage_type = session.get('storage_type', 'container')
    
    # Debug: Check if site and storage_type are set
    if not site:
        flash('Site not selected. Please select a site first.', 'error')
        return redirect(url_for('select_site'))
    
    # Get available sizes
    try:
        import sys
        sys.stderr.write(f"DEBUG: Checking availability for site={site}, storage_type={storage_type}\n")
        sys.stderr.flush()
        available_sizes = storage_finder.get_available_sizes(site, storage_type)
        sys.stderr.write(f"DEBUG: Available sizes returned: {available_sizes}\n")
        sys.stderr.flush()
        if not available_sizes:
            sys.stderr.write(f"DEBUG: No available sizes found, redirecting\n")
            sys.stderr.flush()
            flash('No units currently available at this site. Please try another site.', 'error')
            return redirect(url_for('select_site'))
    except Exception as e:
        import traceback
        import sys
        error_details = traceback.format_exc()
        sys.stderr.write(f"DEBUG: Error in get_available_sizes: {e}\n{error_details}\n")
        sys.stderr.flush()
        flash(f'Error checking availability: {str(e)}', 'error')
        return redirect(url_for('select_site'))
    
    if request.method == 'POST':
        size = request.form.get('size')
        if size and size.isdigit():
            session['selected_size'] = int(size)
            session['items'] = []
            session['unrecognized_items'] = []
            session['prohibited_items'] = []
            return redirect(url_for('show_results'))
        else:
            flash('Please select a valid size', 'error')
    
    return render_template('select_known_size.html', 
                         available_sizes=available_sizes,
                         storage_type=storage_type,
                         site=site)

@app.route('/vehicle-warning', methods=['GET', 'POST'])
def vehicle_warning():
    """Handle vehicle storage warning"""
    if request.method == 'POST':
        switch = request.form.get('switch')
        if switch == 'yes':
            session['storage_type'] = 'container'
            # Need to select site for container storage
            return redirect(url_for('select_site'))
        else:
            flash('Vehicles cannot be stored in internal storage. Please select container storage.', 'error')
            return redirect(url_for('choose_storage_type_for_items'))
    
    return render_template('vehicle_warning.html')

@app.route('/results')
def show_results():
    """Show storage recommendation results"""
    if storage_finder is None:
        flash('Application error: Storage finder module not loaded. Please contact support.', 'error')
        return redirect(url_for('index'))
    
    if 'customer_name' not in session:
        return redirect(url_for('start'))
    
    site = session.get('site')
    storage_type = session.get('storage_type')
    items = session.get('items', [])
    unrecognized = session.get('unrecognized_items', [])
    prohibited = session.get('prohibited_items', [])
    
    # Get size
    if 'selected_size' in session:
        size = session['selected_size']
    elif 'calculated_size' in session:
        size = session['calculated_size']
    else:
        flash('No size information available', 'error')
        return redirect(url_for('find_storage'))
    
    # Get available sizes and pricing
    try:
        available_sizes = storage_finder.get_available_sizes(site, storage_type)
        if not available_sizes:
            return render_template('no_availability.html', site=site)
        
        # Find suitable size
        suitable_size = None
        if items:
            for available_size in available_sizes:
                if available_size >= size:
                    suitable_size = available_size
                    break
        else:
            if size in available_sizes:
                suitable_size = size
            else:
                for available_size in available_sizes:
                    if available_size >= size:
                        suitable_size = available_size
                        break
        
        if not suitable_size:
            return render_template('no_suitable_size.html', 
                                 required_size=size,
                                 available_sizes=available_sizes,
                                 site=site)
        
        # Get pricing
        pricing = None
        if site in storage_finder.SITE_PRICING and storage_type in storage_finder.SITE_PRICING[site]:
            if suitable_size in storage_finder.SITE_PRICING[site][storage_type]:
                pricing = storage_finder.SITE_PRICING[site][storage_type][suitable_size]
        
        # Get contract info
        contract_info = get_contract_info(storage_type)
        
        return render_template('results.html',
                             site=site,
                             storage_type=storage_type,
                             size=suitable_size,
                             items=items,
                             unrecognized=unrecognized,
                             prohibited=prohibited,
                             pricing=pricing,
                             contract_info=contract_info,
                             customer_name=session['customer_name'])
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('find_storage'))

def get_contract_info(storage_type):
    """Get contract information with static prices"""
    if storage_type == 'container':
        return {
            'deposit': STATIC_PRICES['container']['deposit'],
            'lock': STATIC_PRICES['container']['lock'],
            'insurance_rate': 0.99,  # £0.99 per £1k per week
            'insurance_note': 'Does not cover vehicles'
        }
    else:
        return {
            'deposit': STATIC_PRICES['internal']['deposit'],
            'padlock': STATIC_PRICES['internal']['padlock'],
            'insurance_rate': 0.99,  # £0.99 per £1k per week
            'insurance_note': 'Does not cover vehicles'
        }

@app.route('/api/availability/<site>/<storage_type>')
def api_availability(site, storage_type):
    """Get availability for a site and storage type"""
    if storage_finder is None:
        return jsonify({
            'success': False,
            'error': 'Storage finder module not loaded'
        }), 500
    
    try:
        available_sizes = storage_finder.get_available_sizes(site, storage_type)
        return jsonify({
            'success': True,
            'sizes': available_sizes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

