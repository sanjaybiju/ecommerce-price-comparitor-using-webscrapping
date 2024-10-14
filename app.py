from flask import Flask, render_template, request, session, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from firebase_admin import credentials, auth
import firebase_admin
import logging

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' # Secret key for session management

# Firebase initialization
cred = credentials.Certificate(r"C:\project\price-web-d1d1f-firebase-adminsdk-3uwrm-edbdd9aee4.json")
firebase_admin.initialize_app(cred)

# Function to scrape price from Flipkart
def scrape_flipkart(url):
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 20)  # Increase the timeout to 20 seconds
    try:
        # Look for the price with CSS selector
        price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.Nx9bqj")))
        price = price_element.text if price_element else "Price not found"
    except TimeoutException:
        try:
            price_element = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="container"]/div[1]/div[3]/div[1]/div[2]/div[2]/div[1]/div[1]/div[1]/a[1]/div[3]/div[2]/div[1]/div[1]/div[1]')))
            price = price_element.text if price_element else "Price not found"
        except TimeoutException:
            price = "Price not found"
    driver.quit()
    return price

        

# Function to scrape price from Amazon with both CSS selector and XPath
def scrape_amazon(url):
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 20)  # Increase the timeout to 20 seconds
    try:
        # Look for the price with CSS selector first, and if not found, try XPath
        price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.a-price-whole, span.a-color-price")))
        price = price_element.text if price_element else "Price not found"
    except TimeoutException:
        try:
            # Look for the price with XPath if CSS selector didn't find it
            price_element = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="search"]/div[1]/div[1]/div[1]/span[1]/div[1]/div[5]/div[1]/div[1]/span[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[1]/div[1]/a[1]/span[1]/span[2]/span[2], //*[@id="search"]/div[1]/div[1]/div[1]/span[1]/div[1]/div/div[1]/div/div/span[1]')))
            price = price_element.text if price_element else "Price not found"
        except TimeoutException:
            price = "Price not found"
    driver.quit()
    return price


# Function to scrape price from Croma
def scrape_croma(url):
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 20)  # Increase the timeout to 20 seconds
    try:
        # Look for the price with class 'amount' and 'data-testid' attribute set to 'new-price'
        price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.amount[data-testid='new-price']")))
        price = price_element.text.strip() if price_element else "Price not found"
    except TimeoutException:
        price = "Price not found"
    driver.quit()
    return price

# Function to compare prices
def compare_prices(flipkart_price, amazon_price, croma_price):
    prices = {'Flipkart': flipkart_price.replace('₹', '').replace(',', ''),
              'Amazon': amazon_price.replace(',', ''),
              'Croma': croma_price.replace('₹', '').replace(',', '')}
    best_price = min(prices.values())
    best_deal = [merchant for merchant, price in prices.items() if price == best_price][0]
    return best_price, best_deal

# Function to generate product links
def generate_links(product_name):
    try:
        flipkart_link = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&as-pos=1&as-type=HISTORY&sort=popularity"
        amazon_link = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
        croma_link = f"https://www.croma.com/searchB?q={product_name.replace(' ', '%20')}%3Arelevance&text={product_name.replace(' ', '%20')}"

        return [flipkart_link, amazon_link, croma_link]

    except Exception as e:
        print("An error occurred:", e)
        return []

# Register route
def register_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        session['user_email'] = email  # Store user's email in session
        return True
    except ValueError as e:
        logging.error(f"Error during user registration: {e}")
        return str(e)
    except Exception as e:
        logging.error(f"Unexpected error during user registration: {e}")
        return "An error occurred during user registration. Please try again."

# Function to log in an existing user
def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        session['user_email'] = email  # Store user's email in session
        logging.debug("User logged in successfully.")
        return True
    except auth.UserNotFoundError:
        logging.error("User not found.")
        return False
    except Exception as e:
        logging.error(f"Error during user login: {e}")
        return False

# Route for login or registration
# Route for login or registration
@app.route('/', methods=['GET', 'POST'])
def login_or_register():
    if 'user_email' in session:
        return redirect(url_for('home'))  # Redirect to home if user is already logged in

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if 'register' in request.form:
            registration_result = register_user(email, password)
            if registration_result is True:
                return redirect(url_for('home'))  # Redirect to home after successful registration
            else:
                return render_template('login.html', error=registration_result)

        elif 'login' in request.form:
            login_result = login_user(email, password)
            if login_result:
                return redirect(url_for('home'))  # Redirect to home after successful login
            else:
                return render_template('login.html', error="Invalid email or password. Please try again.")

    return render_template('login.html')

# Route for index page
@app.route('/index', methods=['GET', 'POST'])
def home():
    # Check if user is logged in
    if 'user_email' not in session:
        return redirect(url_for('login_or_register'))  # Redirect to login page if not logged in

    if request.method == 'POST':
        product_name = request.form['product_name']

        # Generate links for Flipkart, Amazon, and Croma
        product_links = generate_links(product_name)
        flipkart_link = product_links[0] if len(product_links) > 0 else ""
        amazon_link = product_links[1] if len(product_links) > 1 else ""
        croma_link = product_links[2] if len(product_links) > 2 else ""

        # Scrape prices from the generated links
        flipkart_price = scrape_flipkart(flipkart_link)
        amazon_price = scrape_amazon(amazon_link)
        croma_price = scrape_croma(croma_link)

        # Compare prices and determine the best deal
        best_price, best_deal = compare_prices(flipkart_price, amazon_price, croma_price)

        return render_template('index.html',
                               flipkart_price=flipkart_price,
                               amazon_price=amazon_price,
                               croma_price=croma_price,
                               best_price=best_price,
                               best_deal=best_deal,
                               flipkart_link=flipkart_link,
                               amazon_link=amazon_link,
                               croma_link=croma_link)

    # If it's a GET request or the form is not submitted yet, render the form
    return render_template('index.html')

@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('login_or_register'))

# Add a route to handle adding items to the cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form['product_name']
    # Add the product to the cart (you can store it in session or a database)
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_name)
    return redirect(url_for('home'))  # Redirect back to the home page

# Add a route to handle displaying the cart items
@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items)


if __name__ == '__main__':
    app.run(debug=True)
