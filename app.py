from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'bookstore_secret_2026'

# --- LOCAL EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com' 
app.config['MAIL_PASSWORD'] = 'your-app-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)

# --- DATABASE LOGIC ---

def get_db():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the database tables and adds 30 diverse books with full details."""
    with get_db() as conn:
        # ADDED: Users table creation so registration works
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         email TEXT UNIQUE, password TEXT)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS books 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         title TEXT, author TEXT, price REAL, img TEXT,
                         category TEXT, description TEXT, publisher TEXT, stock INTEGER)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, total REAL, items TEXT, 
                         invoice_no TEXT, address TEXT, method TEXT, 
                         date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS wishlist 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, book_id INTEGER)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS reviews 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         book_id INTEGER, username TEXT, rating INTEGER, comment TEXT)''')
        
        count = conn.execute('SELECT count(*) FROM books').fetchone()[0]
        if count == 0:
            all_books = [
                ('Java: The Complete Reference', 'Herbert Schildt', 850.00, 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400', 'Educational', 'Master Java programming from beginner to advanced.', 'McGraw Hill', 25),
                ('Clean Code', 'Robert C. Martin', 620.00, 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400', 'Educational', 'A handbook of agile software craftsmanship.', 'Prentice Hall', 15),
                ('Effective Java', 'Joshua Bloch', 720.00, 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400', 'Educational', 'Best practices for the Java platform.', 'Addison-Wesley', 10),
                ('Python Crash Course', 'Eric Matthes', 680.00, 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400', 'Educational', 'A hands-on introduction to Python.', 'No Starch Press', 20),
                ('Design Patterns', 'Erich Gamma', 800.00, 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=400', 'Educational', 'Reusable Object-Oriented Software elements.', 'Pearson', 5),
                ('The Pragmatic Programmer', 'Andrew Hunt', 750.00, 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=400', 'Educational', 'Your journey to software development mastery.', 'Addison-Wesley', 12),
                ('Project Hail Mary', 'Andy Weir', 599.00, 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400', 'Fiction', 'A lone survivor must save humanity from disaster.', 'Ballantine', 18),
                ('The Silent Patient', 'Alex Michaelides', 350.00, 'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400', 'Fiction', 'A psychological thriller about a woman’s silence.', 'Celadon Books', 30),
                ('1984', 'George Orwell', 299.00, 'https://images.unsplash.com/photo-1541963463532-d68292c34b19?w=400', 'Fiction', 'Dystopian novel about Big Brother and surveillance.', 'Secker & Warburg', 15),
                ('Dune', 'Frank Herbert', 450.00, 'https://images.unsplash.com/photo-1506466010722-395aa2bef877?w=400', 'Fiction', 'Epic sci-fi masterpiece set on Arrakis.', 'Chilton', 9),
                ('The Alchemist', 'Paulo Coelho', 299.00, 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400', 'Fiction', 'A fable about following your personal legend.', 'HarperOne', 40),
                ('The Great Gatsby', 'F. Scott Fitzgerald', 399.00, 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400', 'Fiction', 'Wealth, love, and the American Dream.', 'Scribner', 22),
                ('Atomic Habits', 'James Clear', 480.00, 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400', 'Non-fiction', 'Build good habits and break bad ones.', 'Penguin', 100),
                ('Sapiens', 'Yuval Noah Harari', 550.00, 'https://images.unsplash.com/photo-1589998059171-988d887df646?w=400', 'Non-fiction', 'A brief history of humankind.', 'Harper', 50),
                ('Thinking, Fast and Slow', 'Daniel Kahneman', 520.00, 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400', 'Non-fiction', 'Systems that drive the way we think.', 'Farrar', 25),
                ('Deep Work', 'Cal Newport', 420.00, 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400', 'Non-fiction', 'Success rules in a distracted world.', 'Grand Central', 35),
                ('The Psychology of Money', 'Morgan Housel', 399.00, 'https://images.unsplash.com/photo-1579621970795-87f9ac756a72?w=400', 'Non-fiction', 'Timeless lessons on wealth and greed.', 'Harriman House', 60),
                ('Quiet', 'Susan Cain', 450.00, 'https://images.unsplash.com/photo-1505935428862-770b6f24f629?w=400', 'Non-fiction', 'The power of introverts in a noisy world.', 'Crown', 14),
                ('Batman: Year One', 'Frank Miller', 600.00, 'https://images.unsplash.com/photo-1588497859490-85d1c17db96d?w=400', 'Comics', 'Gritty reimagining of Batmans first year.', 'DC Comics', 10),
                ('Spider-Man: Blue', 'Jeph Loeb', 450.00, 'https://images.unsplash.com/photo-1612036782180-6f0b6cd846fe?w=400', 'Comics', 'Peter Parker looks back at his lost love.', 'Marvel', 0),
                ('Watchmen', 'Alan Moore', 899.00, 'https://images.unsplash.com/photo-1620336655055-088d06e36bf0?w=400', 'Comics', 'Influential graphic novel about heroes.', 'DC Comics', 5),
                ('The Sandman', 'Neil Gaiman', 950.00, 'https://images.unsplash.com/photo-1541963463532-d68292c34b19?w=400', 'Comics', 'The masterpiece of the King of Dreams.', 'Vertigo', 8),
                ('X-Men: Dark Phoenix', 'Chris Claremont', 700.00, 'https://images.unsplash.com/photo-1635805737707-575885ab0820?w=400', 'Comics', 'The transformation of Jean Grey.', 'Marvel', 12),
                ('Maus', 'Art Spiegelman', 550.00, 'https://images.unsplash.com/photo-1580820269041-35850126943e?w=400', 'Comics', 'Haunting comic about the Holocaust.', 'Pantheon', 4),
                ('Quantitative Aptitude', 'R.S. Aggarwal', 550.00, 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=400', 'Competitive exam books', 'Essential for banking and SSC exams.', 'S. Chand', 150),
                ('Indian Polity', 'M. Laxmikanth', 780.00, 'https://images.unsplash.com/photo-1532153975070-2e9ab71f1b14?w=400', 'Competitive exam books', 'Source for civil services aspirants.', 'McGraw Hill', 80),
                ('Logical Reasoning', 'R.S. Aggarwal', 499.00, 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400', 'Competitive exam books', 'Comprehensive logic guide.', 'S. Chand', 90),
                ('General Knowledge 2026', 'Manohar Pandey', 250.00, 'https://images.unsplash.com/photo-1491843351663-7c1c6c7b89bc?w=400', 'Competitive exam books', 'Latest updates for competitive exams.', 'Arihant', 200),
                ('Objective General English', 'S.P. Bakshi', 320.00, 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400', 'Competitive exam books', 'Mastering English for exams.', 'Arihant', 110),
                ('High School Grammar', 'Wren & Martin', 450.00, 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400', 'Competitive exam books', 'The classic English grammar guide.', 'S. Chand', 100)
            ]
            conn.executemany("INSERT INTO books (title, author, price, img, category, description, publisher, stock) VALUES (?,?,?,?,?,?,?,?)", all_books)
        conn.commit()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/books')
def books():
    if 'user' not in session:
        flash("You must login first to browse books.")
        return redirect(url_for('login'))
        
    db = get_db()
    search_query = request.args.get('search')
    category_query = request.args.get('category')
    
    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (title LIKE ? OR author LIKE ? OR category LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])
    
    if category_query:
        sql += " AND category = ?"
        params.append(category_query)

    all_books = db.execute(sql, params).fetchall()
    categories = db.execute('SELECT DISTINCT category FROM books').fetchall()

    books_with_reviews = []
    for b in all_books:
        revs = db.execute('SELECT * FROM reviews WHERE book_id = ?', (b['id'],)).fetchall()
        books_with_reviews.append({'details': b, 'reviews': revs})
        
    return render_template('books.html', books=books_with_reviews, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()  # .strip() removes accidental spaces
        password = request.form.get('password').strip()
        
        db = get_db()
        # We fetch the user by email
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user:
            # Check if the password matches exactly
            if user['password'] == password:
                session['user'] = email
                flash("Login successful!")
                return redirect(url_for('books'))
            else:
                # Email exists, but password was wrong
                flash("Incorrect password. Please try again.")
                return render_template('login.html', show_forgot=True)
        else:
            # Email doesn't exist in the database at all
            flash("No account found with that email. Please register.")
            return redirect(url_for('register'))
            
    return render_template('login.html')
 

@app.route('/register', methods=['GET', 'POST'])
def register():
    # CHANGED: Now saves user to database
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        db = get_db()
        try:
            db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            db.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except:
            flash("Email already registered.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/account')
def account():
    if 'user' not in session:
        flash("Please login to view your profile.")
        return redirect(url_for('login'))
    
    db = get_db()
    orders = db.execute('SELECT * FROM orders WHERE username = ? ORDER BY date DESC', (session['user'],)).fetchall()
    wishlist = db.execute('''SELECT b.* FROM books b 
                            JOIN wishlist w ON b.id = w.book_id 
                            WHERE w.username = ?''', (session['user'],)).fetchall()
    user_reviews = db.execute('''SELECT r.*, b.title FROM reviews r 
                                JOIN books b ON r.book_id = b.id 
                                WHERE r.username = ?''', (session['user'],)).fetchall()

    return render_template('account.html', username=session['user'], orders=orders, wishlist=wishlist, reviews=user_reviews)

@app.route('/add_to_wishlist/<int:book_id>')
def add_to_wishlist(book_id):
    if 'user' not in session:
        flash("Please login to use Wishlist.")
        return redirect(url_for('login'))
    db = get_db()
    exists = db.execute('SELECT * FROM wishlist WHERE username = ? AND book_id = ?', (session['user'], book_id)).fetchone()
    if not exists:
        db.execute('INSERT INTO wishlist (username, book_id) VALUES (?,?)', (session['user'], book_id))
        db.commit()
        flash("Added to Wishlist!")
    return redirect(url_for('books'))

@app.route('/submit_review/<int:book_id>', methods=['POST'])
def submit_review(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    db = get_db()
    db.execute('INSERT INTO reviews (book_id, username, rating, comment) VALUES (?,?,?,?)', (book_id, session['user'], rating, comment))
    db.commit()
    flash("Review submitted!")
    return redirect(url_for('books'))

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart_ids = session.get('cart', [])
    db = get_db()
    items = []
    total = 0
    for b_id in cart_ids:
        book = db.execute('SELECT * FROM books WHERE id = ?', (b_id,)).fetchone()
        if book:
            items.append(book)
            total += book['price']
    return render_template('cart.html', items=items, total=total)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    cart.append(book_id)
    session['cart'] = cart
    flash("Book added to cart!")
    return redirect(url_for('books'))

@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    if 'cart' in session:
        cart = session['cart']
        if 0 <= index < len(cart):
            cart.pop(index)
            session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user' not in session or not session.get('cart'):
        return redirect(url_for('books'))
    db = get_db()
    total = sum(db.execute('SELECT price FROM books WHERE id = ?', (b_id,)).fetchone()['price'] for b_id in session['cart'])
    return render_template('checkout.html', total=total)

@app.route('/success', methods=['POST'])
def success():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_name = request.form.get('name')
    address = request.form.get('address')
    method = request.form.get('payment_method')
    
    cart_ids = session.get('cart', [])
    db = get_db()
    titles = []
    total = 0
    items_list = []
    
    for b_id in cart_ids:
        book = db.execute('SELECT * FROM books WHERE id = ?', (b_id,)).fetchone()
        if book:
            titles.append(book['title'])
            total += book['price']
            items_list.append(book)
    
    invoice_no = f"INV-2026-{random.randint(10000, 99999)}"
    
    db.execute('INSERT INTO orders (username, total, items, invoice_no, address, method) VALUES (?,?,?,?,?,?)',
                (session['user'], total, ", ".join(titles), invoice_no, address, method))
    db.commit()
    
    session.pop('cart', None)
    
    return render_template('ordersuccess.html', total=total, invoice_no=invoice_no, items=items_list, user_name=user_name, address=address, method=method)

# --- ADMIN PORTAL ---

@app.route('/adminlogin')
def admin_login_page():
    return render_template('adminlogin.html')

@app.route('/admin_auth', methods=['POST'])
def admin_auth():
    user = request.form.get('username')
    pwd = request.form.get('password')
    
    if user == 'admin':
        if pwd == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('admin'))
        else:
            flash("Invalid Password!")
            return redirect(url_for('admin_login_page', show_forgot=True))
            
    flash("Invalid Admin Credentials!")
    return redirect(url_for('admin_login_page'))

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('admin_login_page'))
    
    db = get_db()
    all_books = db.execute('SELECT * FROM books').fetchall()
    all_orders = db.execute('SELECT * FROM orders ORDER BY date DESC').fetchall()
    
    return render_template('admin.html', books=all_books, orders=all_orders)

@app.route('/admin/add', methods=['POST'])
def add_book():
    if session.get('user') == 'admin':
        db = get_db()
        db.execute('''INSERT INTO books (title, author, price, img, category, description, publisher, stock) 
                      VALUES (?,?,?,?,?,?,?,?)''', 
                    (request.form.get('title'), request.form.get('author'), 
                     float(request.form.get('price', 0)), request.form.get('img'),
                     request.form.get('category', 'General'), request.form.get('description', ''), 
                     request.form.get('publisher', 'Unknown'), int(request.form.get('stock', 0))))
        db.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:book_id>')
def delete_book(book_id):
    if session.get('user') == 'admin':
        db = get_db()
        db.execute('DELETE FROM books WHERE id = ?', (book_id,))
        db.commit()
    return redirect(url_for('admin'))

# --- PASSWORD RESET & RECOVERY ROUTES ---

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/reset_request', methods=['POST'])
def reset_request():
    email = request.form.get('email')
    if email:
        flash(f"Verification successful for {email}. Please set your new password.")
        return redirect(url_for('reset_password_page', email=email))
    return redirect(url_for('forgot_password'))

@app.route('/reset_password_page')
def reset_password_page():
    email = request.args.get('email')
    return render_template('reset_password.html', email=email)

@app.route('/update_password', methods=['POST'])
def update_password():
    # CHANGED: Now updates password in the database
    email = request.form.get('email')
    new_pwd = request.form.get('new_password')
    db = get_db()
    db.execute('UPDATE users SET password = ? WHERE email = ?', (new_pwd, email))
    db.commit()
    flash("Success! Password updated. You can now login.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)