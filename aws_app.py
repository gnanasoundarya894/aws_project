 from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
import random
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'techbooks_aws_secret_key'

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

# SNS Configuration
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:604665149129:aws_capstone_topic' 

def send_notification(subject, message):
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print(f"SNS Error: {e}")

# --- CORE ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/books')
def books():
    if 'user' not in session:
        flash("You must login first to browse books.")
        return redirect(url_for('login'))
        
    query = request.args.get('search')
    if query:
        # Search functionality using DynamoDB Scan with Filter
        response = books_table.scan(
            FilterExpression=Attr('title').contains(query) | Attr('author').contains(query)
        )
    else:
        response = books_table.scan()

    all_books = response.get('Items', [])
    books_with_reviews = []
    
    for b in all_books:
        # Fetch reviews for this specific book
        rev_res = reviews_table.scan(FilterExpression=Attr('book_id').eq(b['id']))
        books_with_reviews.append({'details': b, 'reviews': rev_res.get('Items', [])})
        
    return render_template('books.html', books=books_with_reviews)

# --- WISHLIST & REVIEWS ---

@app.route('/add_to_wishlist/<book_id>')
def add_to_wishlist(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    
    wishlist_id = str(uuid.uuid4())
    wishlist_table.put_item(Item={
        'wishlist_id': wishlist_id,
        'username': session['user'],
        'book_id': book_id
    })
    flash("Added to Wishlist!")
    return redirect(url_for('books'))

@app.route('/submit_review/<book_id>', methods=['POST'])
def submit_review(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    
    review_id = str(uuid.uuid4())
    reviews_table.put_item(Item={
        'review_id': review_id,
        'book_id': book_id,
        'username': session['user'],
        'rating': int(request.form.get('rating')),
        'comment': request.form.get('comment')
    })
    flash("Review submitted!")
    return redirect(url_for('books'))

# --- CART & CHECKOUT ---

@app.route('/add_to_cart/<book_id>')
def add_to_cart(book_id):
    if 'user' not in session: return redirect(url_for('login'))
    cart = session.get('cart', [])
    cart.append(book_id)
    session['cart'] = cart
    flash("Added to cart!")
    return redirect(url_for('books'))

@app.route('/success', methods=['POST'])
def success():
    if 'user' not in session: return redirect(url_for('login'))

    cart_ids = session.get('cart', [])
    titles = []
    total = 0
    
    for bid in cart_ids:
        res = books_table.get_item(Key={'id': str(bid)})
        if 'Item' in res:
            total += float(res['Item']['price'])
            titles.append(res['Item']['title'])
    
    invoice_no = f"INV-{random.randint(10000, 99999)}"
    
    # Store Order in AWS
    orders_table.put_item(Item={
        'order_id': str(uuid.uuid4()),
        'username': session['user'],
        'total': total,
        'items': ", ".join(titles),
        'invoice_no': invoice_no,
        'date': datetime.now().isoformat()
    })
    
    send_notification("New Sale!", f"User {session['user']} bought: {', '.join(titles)}. Total: ${total}")
    session.pop('cart', None)
    return render_template('ordersuccess.html', invoice_no=invoice_no, total=total)

# --- ADMIN FEATURES ---

@app.route('/admin/add', methods=['POST'])
def add_book():
    if session.get('user') == 'admin':
        book_id = str(uuid.uuid4())
        books_table.put_item(Item={
            'id': book_id,
            'title': request.form['title'],
            'author': request.form['author'],
            'price': float(request.form['price']),
            'img': request.form['img']
        })
    return redirect(url_for('admin'))

# --- AUTH ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        res = users_table.get_item(Key={'username': username})
        if 'Item' in res and res['Item']['password'] == password:
            session['user'] = username
            return redirect(url_for('books'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)