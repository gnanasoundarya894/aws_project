from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
import random
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'bookstore_aws_2026_secret'

# --- AWS CONFIGURATION ---
REGION = 'us-east-1' 
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

# DynamoDB Table Connections
books_table = dynamodb.Table('Books')
orders_table = dynamodb.Table('Orders')
wishlist_table = dynamodb.Table('Wishlist')
reviews_table = dynamodb.Table('Reviews')
users_table = dynamodb.Table('Users')

# SNS Topic
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:396913721135:bookbazaar' 

def send_notification(subject, message):
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print(f"SNS Error: {e}")

# --- AUTHENTICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        
        response = users_table.get_item(Key={'username':email})
        user = response.get('Item')
        if user and user['password'] == password:
            session['user'] = email
            flash("Login successful!")
            if email == 'admin' or email == 'admin@gmail.com':
                return redirect(url_for('admin'))
            return redirect(url_for('books'))
        else:
            flash("Invalid email or password!")
            return render_template('login.html', show_forgot=True)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            users_table.put_item(
                Item={'email': email, 'password': password},
                ConditionExpression='attribute_not_exists(email)'
            )
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except ClientError:
            flash("Email already registered.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('home'))

# --- BOOK BROWSING ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/books')
def books():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    search_query = request.args.get('search')
    category_query = request.args.get('category')
    
    if search_query:
        response = books_table.scan(FilterExpression=Attr('title').contains(search_query) | Attr('author').contains(search_query))
    elif category_query:
        response = books_table.scan(FilterExpression=Attr('category').eq(category_query))
    else:
        response = books_table.scan()

    all_books = response.get('Items', [])
    categories = list(set([b['category'] for b in all_books if 'category' in b]))

    books_with_reviews = []
    for b in all_books:
        rev_res = reviews_table.scan(FilterExpression=Attr('book_id').eq(b['id']))
        books_with_reviews.append({'details': b, 'reviews': rev_res.get('Items', [])})
        
    return render_template('books.html', books=books_with_reviews, categories=categories)

# --- WISHLIST & REVIEWS ---

@app.route('/add_to_wishlist/<book_id>')
def add_to_wishlist(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    wishlist_table.put_item(Item={
        'wish_id': str(uuid.uuid4()),
        'username': session['user'],
        'book_id': str(book_id)
    })
    flash("Added to Wishlist!")
    return redirect(url_for('books'))

@app.route('/submit_review/<book_id>', methods=['POST'])
def submit_review(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    reviews_table.put_item(Item={
        'review_id': str(uuid.uuid4()),
        'book_id': str(book_id),
        'username': session['user'],
        'rating': int(request.form.get('rating')),
        'comment': request.form.get('comment')
    })
    flash("Review submitted!")
    return redirect(url_for('books'))

# --- CART & CHECKOUT ---

@app.route('/cart')
def cart():
    if 'user' not in session: return redirect(url_for('login'))
    cart_ids = session.get('cart', [])
    items = []
    total = 0
    for b_id in cart_ids:
        res = books_table.get_item(Key={'id': str(b_id)})
        if 'Item' in res:
            items.append(res['Item'])
            total += float(res['Item']['price'])
    return render_template('cart.html', items=items, total=total)

@app.route('/add_to_cart/<book_id>')
def add_to_cart(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    cart = session.get('cart', [])
    cart.append(str(book_id))
    session['cart'] = cart
    flash("Added to cart!")
    return redirect(url_for('books'))

@app.route('/success', methods=['POST'])
def success():
    if 'user' not in session: return redirect(url_for('login'))
    
    address = request.form.get('address')
    method = request.form.get('payment_method')
    cart_ids = session.get('cart', [])
    titles = []
    total = 0
    
    for b_id in cart_ids:
        res = books_table.get_item(Key={'id': str(b_id)})
        if 'Item' in res:
            book = res['Item']
            titles.append(book['title'])
            total += float(book['price'])
    
    invoice_no = f"INV-AWS-{random.randint(10000, 99999)}"
    orders_table.put_item(Item={
        'order_id': str(uuid.uuid4()),
        'username': session['user'],
        'total': total,
        'items': ", ".join(titles),
        'invoice_no': invoice_no,
        'address': address,
        'method': method,
        'date': datetime.now().isoformat()
    })
    
    send_notification("New Sale!", f"Order {invoice_no} by {session['user']}. Total: ${total}")
    session.pop('cart', None)
    return render_template('ordersuccess.html', total=total, invoice_no=invoice_no)

# --- ADMIN PORTAL ---

@app.route('/admin')
def admin():
    if session.get('user') != 'admin': return redirect(url_for('login'))
    books = books_table.scan().get('Items', [])
    orders = orders_table.scan().get('Items', [])
    return render_template('admin.html', books=books, orders=orders)

@app.route('/admin/add', methods=['POST'])
def add_book():
    if session.get('user') == 'admin':
        book_id = str(uuid.uuid4())
        books_table.put_item(Item={
            'id': book_id,
            'title': request.form['title'],
            'author': request.form['author'],
            'price': float(request.form['price']),
            'img': request.form['img'],
            'category': request.form.get('category', 'General'),
            'description': request.form.get('description', ''),
            'stock': int(request.form.get('stock', 0))
        })
    return redirect(url_for('admin'))

@app.route('/admin/delete/<book_id>')
def delete_book(book_id):
    if session.get('user') == 'admin':
        books_table.delete_item(Key={'id': str(book_id)})
    return redirect(url_for('admin'))

# --- PASSWORD RECOVERY ---
@app.route('/forgot_password') # or whatever your route is
def forgot_password():         # Change this name here!
    email = request.form.get('email')
    new_pwd = request.form.get('new_password')
    users_table.update_item(
        Key={'username': email},
        UpdateExpression="SET password = :p",
        ExpressionAttributeValues={':p': new_pwd}
    )
    flash("Password updated successfully!")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
