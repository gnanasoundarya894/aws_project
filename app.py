from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message  # Added for local email support
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
    """Creates the database tables and adds 30 diverse books if empty."""
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS books 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         title TEXT, author TEXT, price REAL, img TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, total REAL, items TEXT, 
                         invoice_no TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS wishlist 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         username TEXT, book_id INTEGER)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS reviews 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         book_id INTEGER, username TEXT, rating INTEGER, comment TEXT)''')
        
        count = conn.execute('SELECT count(*) FROM books').fetchone()[0]
        if count == 0:
            all_books = [
                ('Java: The Complete Reference', 'Herbert Schildt', 850.00, 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&q=80'),
                ('Effective Java', 'Joshua Bloch', 720.00, 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&q=80'),
                ('Head First Java', 'Kathy Sierra', 580.00, 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=400&q=80'),
                ('Java Concurrency', 'Brian Goetz', 900.00, 'https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=400&q=80'),
                ('Core Java Volume I', 'Cay S. Horstmann', 780.00, 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=400&q=80'),
                ('HTML and CSS: Design', 'Jon Duckett', 500.00, 'https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=400&q=80'),
                ('CSS Secrets', 'Lea Verou', 450.00, 'https://images.unsplash.com/photo-1523437113738-bbd3cc89fb19?w=400&q=80'),
                ('Responsive Web Design', 'Ethan Marcotte', 350.00, 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&q=80'),
                ('CSS: Definitive Guide', 'Eric Meyer', 600.00, 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=400&q=80'),
                ('Learning Web Design', 'Jennifer Robbins', 520.00, 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400&q=80'),
                ('Intro to Algorithms', 'Thomas Cormen', 1200.00, 'https://images.unsplash.com/photo-1509228468518-180dd4864904?w=400&q=80'),
                ('Data Structures in Java', 'Robert Lafore', 640.00, 'https://images.unsplash.com/photo-1516259762381-22954d7d3ad2?w=400&q=80'),
                ('Algorithm Design Manual', 'Steven Skiena', 850.00, 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=400&q=80'),
                ('Algorithms', 'Robert Sedgewick', 920.00, 'https://images.unsplash.com/photo-1551033406-611cf9a28f67?w=400&q=80'),
                ('Cracking the Interview', 'Gayle McDowell', 790.00, 'https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=400&q=80'),
                ('Clean Code', 'Robert C. Martin', 620.00, 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&q=80'),
                ('Pragmatic Programmer', 'Andrew Hunt', 600.00, 'https://images.unsplash.com/photo-1510915228340-29c85a43dcfe?w=400&q=80'),
                ('Design Patterns', 'Erich Gamma', 800.00, 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=400&q=80'),
                ('Compilers', 'Alfred Aho', 950.00, 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&q=80'),
                ('Modern OS', 'Andrew Tanenbaum', 1100.00, 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&q=80'),
                ('Project Hail Mary', 'Andy Weir', 599.00, 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&q=80'),
                ('The Silent Patient', 'Alex Michaelides', 350.00, 'https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&q=80'),
                ('Atomic Habits', 'James Clear', 480.00, 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80'),
                ('Dune', 'Frank Herbert', 450.00, 'https://images.unsplash.com/photo-1506466010722-395aa2bef877?w=400&q=80'),
                ('Psychology of Money', 'Morgan Housel', 399.00, 'https://images.unsplash.com/photo-1579621970795-87f9ac756a72?w=400&q=80'),
                ('The Alchemist', 'Paulo Coelho', 299.00, 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&q=80'),
                ('Search for Meaning', 'Viktor Frankl', 320.00, 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80'),
                ('Deep Work', 'Cal Newport', 420.00, 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&q=80'),
                ('Sherlock Holmes', 'Conan Doyle', 899.00, 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=400&q=80'),
                ('Sapiens', 'Yuval Noah Harari', 550.00, 'https://images.unsplash.com/photo-1589998059171-988d887df646?w=400&q=80')
            ]
            conn.executemany("INSERT INTO books (title, author, price, img) VALUES (?,?,?,?)", all_books)
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
    query = request.args.get('search')
    
    if query:
        search_term = f"%{query}%"
        all_books = db.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", (search_term, search_term)).fetchall()
    else:
        all_books = db.execute('SELECT * FROM books').fetchall()

    # Pass books AND their reviews to the template
    books_with_reviews = []
    for b in all_books:
        revs = db.execute('SELECT * FROM reviews WHERE book_id = ?', (b['id'],)).fetchall()
        books_with_reviews.append({'details': b, 'reviews': revs})
        
    return render_template('books.html', books=books_with_reviews)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['user'] = username
        if username == 'admin':
            return redirect(url_for('admin_login_page'))
        return redirect(url_for('books'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash("Registration successful! Please login.")
        return redirect(url_for('login'))
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
    # Fetch user's orders
    orders = db.execute('SELECT * FROM orders WHERE username = ? ORDER BY date DESC', (session['user'],)).fetchall()
    
    # Fetch user's wishlist items
    wishlist = db.execute('''SELECT b.* FROM books b 
                            JOIN wishlist w ON b.id = w.book_id 
                            WHERE w.username = ?''', (session['user'],)).fetchall()
    
    # Fetch reviews written by the user
    user_reviews = db.execute('''SELECT r.*, b.title FROM reviews r 
                                JOIN books b ON r.book_id = b.id 
                                WHERE r.username = ?''', (session['user'],)).fetchall()

    return render_template('account.html', username=session['user'], orders=orders, wishlist=wishlist, reviews=user_reviews)

# --- WISHLIST & REVIEW ROUTES ---

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
    else:
        flash("Book is already in your wishlist.")
    return redirect(url_for('books'))

@app.route('/submit_review/<int:book_id>', methods=['POST'])
def submit_review(book_id):
    if 'user' not in session:
        flash("Please login to submit a review.")
        return redirect(url_for('login'))
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    db = get_db()
    db.execute('INSERT INTO reviews (book_id, username, rating, comment) VALUES (?,?,?,?)', (book_id, session['user'], rating, comment))
    db.commit()
    flash("Review submitted!")
    return redirect(url_for('books'))

# --- CART LOGIC ---

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    cart_ids = session.get('cart', [])
    db = get_db()
    items = []
    total = 0
    for book_id in cart_ids:
        book = db.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if book:
            items.append(book)
            total += book['price']
    return render_template('cart.html', items=items, total=total)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user' not in session:
        flash("Please login to shop.")
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
            flash("Item removed.")
    return redirect(url_for('cart'))

# --- CHECKOUT & RECEIPT LOGIC ---

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if not session.get('cart'):
        return redirect(url_for('books'))
    
    cart_ids = session.get('cart', [])
    db = get_db()
    total = 0
    for book_id in cart_ids:
        book = db.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if book:
            total += book['price']
    return render_template('checkout.html', total=total)

@app.route('/success', methods=['POST'])
def success():
    if 'user' not in session:
        return redirect(url_for('login'))

    customer_name = request.form.get('name', 'Valued Customer')
    customer_email = request.form.get('email')
    customer_address = request.form.get('address', 'Address Not Provided')
    payment_method = request.form.get('payment_method', 'Paid')
    
    cart_ids = session.get('cart', [])
    db = get_db()
    items = []
    titles = []
    total = 0
    for book_id in cart_ids:
        book = db.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if book:
            items.append(book)
            titles.append(book['title'])
            total += book['price']
    
    invoice_no = f"INV-{random.randint(10000, 99999)}"

    # 1. Save to Database
    db.execute('INSERT INTO orders (username, total, items, invoice_no) VALUES (?,?,?,?)',
                (session['user'], total, ", ".join(titles), invoice_no))
    db.commit()
    
    # 2. Send Local Email Notification
    if customer_email:
        try:
            msg = Message(f"Order Confirmation: {invoice_no}",
                            recipients=[customer_email])
            msg.body = f"Hello {customer_name},\n\nYour order for {', '.join(titles)} was successful!\nTotal: ${total}\nAddress: {customer_address}\n\nThank you for shopping at TechBooks!"
            mail.send(msg)
        except Exception as e:
            print(f"Mail delivery failed: {e}")

    session.pop('cart', None)
    
    return render_template('ordersuccess.html', 
                            name=customer_name, 
                            address=customer_address, 
                            method=payment_method, 
                            items=items, 
                            total=total,
                            invoice_no=invoice_no)

# --- ADMIN PORTAL ---

@app.route('/adminlogin')
def admin_login_page():
    return render_template('adminlogin.html')

@app.route('/admin_auth', methods=['POST'])
def admin_auth():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'admin' and password == 'admin123':
        session['user'] = 'admin'
        flash("Admin Login Successful!")
        return redirect(url_for('admin'))
    else:
        flash("Invalid Admin Credentials!")
        return redirect(url_for('admin_login_page'))

@app.route('/admin')
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('admin_login_page'))
    db = get_db()
    all_books = db.execute('SELECT * FROM books').fetchall()
    return render_template('admin.html', books=all_books)

@app.route('/admin/add', methods=['POST'])
def add_book():
    if session.get('user') == 'admin':
        db = get_db()
        db.execute('INSERT INTO books (title, author, price, img) VALUES (?,?,?,?)', 
                    (request.form['title'], request.form['author'], float(request.form['price']), request.form['img']))
        db.commit()
        flash("Book added to the database.")
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:book_id>')
def delete_book(book_id):
    if session.get('user') == 'admin':
        db = get_db()
        db.execute('DELETE FROM books WHERE id = ?', (book_id,))
        db.commit()
        flash("Book removed from the database.")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)