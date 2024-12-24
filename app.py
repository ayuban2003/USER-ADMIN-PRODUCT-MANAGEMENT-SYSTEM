from pkgutil import get_data
from flask import Flask, flash, render_template, request, redirect, send_from_directory, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os 

app = Flask(__name__, template_folder='template')
app.secret_key = '3a1b4c5d6e7f8a9b0c9d9e0f1d1e2a3b'
print(os.urandom(24).hex())

# Database connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="info"
)

mycursor = mydb.cursor(buffered=True)

# Helper function to check if user is logged in and has a specific role
def is_logged_in(role=None):
    if 'user_id' not in session:
        return False
    if role:
        sql = "SELECT role FROM info_user WHERE id = %s"
        mycursor.execute(sql, (session['user_id'],))
        user_role = mycursor.fetchone()[0]
        return user_role == role
    return True

# Home route
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

# Registration (Sign-up) route with role selection
@app.route('/register', methods=['GET', 'POST'])
def register():
    success_message = None
    error_message = None
    if request.method == 'POST':
        role = request.form['role']
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        contact_number = request.form['contact_number']
        email_address = request.form['email_address']
        address = request.form['address']
        password = request.form['password']

        # Hash the password securely
        hashed_password = generate_password_hash(password)

        try:
            # Check if email already exists
            sql = "SELECT email_address FROM info_user WHERE email_address = %s"
            mycursor.execute(sql, (email_address,))
            if mycursor.fetchone():
                error_message = "Account already existed. Please try again."
            else:
                # Insert new user
                sql = """
                    INSERT INTO info_user (
                        first_name, middle_name, last_name, contact_number, email_address, address, password, role
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                val = (first_name, middle_name, last_name, contact_number, email_address, address, hashed_password, role)
                mycursor.execute(sql, val)
                mydb.commit()
                success_message = "You have successfully created an account. Please go back to Login."

        except mysql.connector.Error as err:
            error_message = f"Database error: {err}"

    return render_template('register.html', success_message=success_message, error_message=error_message)


# Login route with role selection
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        email_address = request.form['email_address']
        password = request.form['password']

        try:
            # Query the database for the user
            sql = "SELECT id, password, role, first_name FROM info_user WHERE email_address = %s"
            mycursor.execute(sql, (email_address,))
            result = mycursor.fetchone()

            if result:
                if check_password_hash(result[1], password):  # If password is correct
                    if result[2] == role:  # Check if the role matches
                        session['user_id'] = result[0]
                        session['role'] = result[2]
                        session['first_name'] = result[3]
                        print(session)

                        # Redirect based on role
                        if role == 'Admin':
                            return redirect(url_for('admin_dashboard'))
                        elif role == 'User':
                            return redirect(url_for('user_dashboard'))

                # Password incorrect or role mismatch
                error_message = "Incorrect password or role mismatch. Please try again."
                return render_template('login.html', error_message=error_message)
            else:
                # No user found with that email
                error_message = "Email not found. Please try again."
                return render_template('login.html', error_message=error_message)

        except mysql.connector.Error as err:
            return f"Database error: {err}"

    return render_template('login.html')

#  ----------------- DASHBOARD routes -----------------#

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'User':
        return redirect(url_for('login'))  # Redirect to login if not logged in as Regular User
    return render_template('user_dashboard.html', user=session)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))  # Redirect to login if not logged in as Admin
    return render_template('admin_dashboard.html', user=session)

# ----------------- Product Management routes -----------------#

@app.route('/view_products')
def view_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in

    # Fetch all products from the database
    mycursor.execute("SELECT id, product_name, description, price, quantity FROM products")
    products = mycursor.fetchall()

    return render_template('view_products.html', products=products)

@app.route('/buy_products')
def buy_products():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    product_id = request.args.get('product_id', type=int)  # Get product ID from the URL

    # Fetch product details based on product_id
    try:
        mycursor.execute("SELECT product_name, description, price, quantity FROM products WHERE id = %s", (product_id,))
        product = mycursor.fetchone()

        if not product:
            return "Product not found"

        product_name, description, price, quantity = product

        # Check if there's enough stock for the product
        if quantity <= 0:
            return "Sorry, this product is out of stock."

        # Process the purchase by deducting the quantity
        new_quantity = quantity - 1
        mycursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_quantity, product_id))
        mydb.commit()

        # Insert the purchase into the 'orders' table
        user_id = session['user_id']
        total_amount = price  # Assuming user buys one unit of the product
        mycursor.execute("""
            INSERT INTO orders (user_id, product_id, total_amount, status)
            VALUES (%s, %s, %s, 'Completed')
        """, (user_id, product_id, total_amount))
        mydb.commit()

        # Display a confirmation message
        return render_template('receipt.html', product_name=product_name, price=price, total_amount=total_amount)

    except mysql.connector.Error as err:
        return f"Database error: {err}"

@app.route('/purchase_product/<int:product_id>', methods=['POST'])
def purchase_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch product details
    mycursor.execute("SELECT product_name, price, quantity FROM products WHERE id = %s", (product_id,))
    product = mycursor.fetchone()

    if not product:
        return "Product not found"
    if product[2] <= 0:
        return "Sorry, this product is out of stock."

    # Reduce stock by 1
    new_quantity = product[2] - 1
    mycursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_quantity, product_id))
    mydb.commit()

    # Add purchase to orders table
    mycursor.execute("""
        INSERT INTO orders (user_id, product_id, total_amount, status)
        VALUES (%s, %s, %s, 'Pending')
    """, (user_id, product_id, product[1]))
    mydb.commit()

    return redirect(url_for('receipt'))  # Redirect to the receipt page

@app.route('/receipt')
def receipt():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch user's orders from the database
    mycursor.execute("""
        SELECT o.id, p.product_name, o.total_amount, o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = %s
    """, (user_id,))
    orders = mycursor.fetchall()

    return render_template('receipt.html', orders=orders)

# ----------------- User Profile routes -----------------#

@app.route('/change_user_info', methods=['GET', 'POST'])
def change_user_info():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in
    
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')  # Default to empty string if not provided
        last_name = request.form['last_name']
        contact_number = request.form['contact_number']
        address = request.form['address']
        
        # Perform some basic validation
        if not first_name or not last_name:
            error_message = "First name and last name are required."
            return render_template('change_user_info.html', user_data=request.form, error_message=error_message)
        
        # Update user data in the database
        try:
            sql = """
                UPDATE info_user SET first_name = %s, middle_name = %s, last_name = %s, 
                contact_number = %s, address = %s WHERE id = %s
            """
            mycursor.execute(sql, (first_name, middle_name, last_name, contact_number, address, session['user_id']))
            mydb.commit()
            
            # Redirect to the success page after successful update
            return redirect(url_for('success'))

        except mysql.connector.Error as err:
            error_message = f"An error occurred while updating your information: {err}"
            return render_template('change_user_info.html', user_data=request.form, error_message=error_message)
    
    # Fetch user data to pre-fill in the form
    sql = "SELECT first_name, middle_name, last_name, contact_number, address FROM info_user WHERE id = %s"
    mycursor.execute(sql, (session['user_id'],))
    user_data = mycursor.fetchone()

    return render_template('change_user_info.html', user_data=user_data)


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        
        # Fetch the current user's password from the database
        sql = "SELECT password FROM info_user WHERE id = %s"
        mycursor.execute(sql, (session['user_id'],))
        user = mycursor.fetchone()

        if not user or not check_password_hash(user[0], old_password):
            # If old password is incorrect
            message = "Old password is incorrect."
            message_type = "error"
            return render_template('change_password.html', message=message, message_type=message_type)
        
        if new_password != confirm_new_password:
            # If new passwords do not match
            message = "New passwords do not match."
            message_type = "error"
            return render_template('change_password.html', message=message, message_type=message_type)

        # Update the password in the database
        hashed_password = generate_password_hash(new_password)
        sql = "UPDATE info_user SET password = %s WHERE id = %s"
        mycursor.execute(sql, (hashed_password, session['user_id']))
        mydb.commit()

        # Show success message and redirect
        message = "Your password has been changed successfully!"
        message_type = "success"
        return render_template('change_password.html', message=message, message_type=message_type)

    return render_template('change_password.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)