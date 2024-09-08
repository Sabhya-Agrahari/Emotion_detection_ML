import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image, ImageTk
import os
import random
import smtplib
import numpy as np
import cv2
from tensorflow.keras.models import model_from_json # type: ignore
from geopy.geocoders import Nominatim 
from geopy.exc import GeocoderInsufficientPrivileges # type: ignore
import pytz
import requests
from datetime import datetime
import speech_recognition as sr
import pyaudio


# Initialize the main application window
class MultiPageApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Multi-Page Tkinter Application")
        self.geometry("1000x800")
        
        # Container to hold all pages, using grid
        container = tk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")  # Use grid instead of pack

        self.frames = {}
        
        # Add each page to the frames dictionary
        self.page_order = [EmotionDetectionPage, LoginSignupPage, DeliveryAddressPage, WeatherPage, CouponPage, VoiceProductSearchPage]
        self.current_page = 0    
        for F in self.page_order:
            page_name = F.__name__
            frame = F(parent=container, controller=self)  # Parent is now container, not self
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self.page_order[self.current_page].__name__)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def navigate_next(self):
        if self.current_page < len(self.page_order) - 1:
            self.current_page += 1
            self.show_frame(self.page_order[self.current_page].__name__)

    def navigate_back(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_frame(self.page_order[self.current_page].__name__)

# Emotion Detection Page
class EmotionDetectionPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up UI components
        self.label1 = Label(self, background='#CDCDCD', font=('arial', 15, 'bold'))
        self.sign_image = Label(self)


        inner_frame = tk.Frame(self)  # Create an inner frame for the content
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)  # Add padding for better visual layout

        # Configure the inner frame for centering widgets
        inner_frame.grid_rowconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(0, weight=1)

        # Load the model and the face cascade
        self.facec = cv2.CascadeClassifier("haarcascades_frontalface_default.xml")
        self.model = self.FacialExpressionModel("model_a.json", "model_weights.weights.h5")
        self.EMOTION_LIST = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]

        # Heading
        heading = Label(self, text="Emotion Detector", pady=20, font=('arial', 25, 'bold'))
        heading.configure(background="#CDCDCD", foreground="#364156")
        heading.grid(row=0, column=0, columnspan=2, pady=20)

        # Upload button
        upload = Button(self, text="Upload Image", command=self.upload_image, padx=10, pady=5)
        upload.configure(background="#361456", foreground='white', font=('arial', 20, 'bold'))
        upload.grid(row=3, column=0, columnspan=2, pady=50)

        # Set labels
        self.sign_image.grid(row=2, column=0, columnspan=2, pady=20)
        self.label1.grid(row=1, column=0, columnspan=2, pady=20)

        # Add navbar
        self.create_navbar(controller)

    def create_navbar(self, controller):
        navbar_frame = tk.Frame(self)
        navbar_frame.grid(row=4, column=0, columnspan=2, pady=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=controller.navigate_back)
        back_button.grid(row=0, column=0, padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=controller.navigate_next)
        next_button.grid(row=0, column=1, padx=20)

    def FacialExpressionModel(self, json_file, weights_file):
        with open(json_file, "r") as file:
            loaded_model_json = file.read()
            model = model_from_json(loaded_model_json)

        model.load_weights(weights_file)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def Detect(self, file_path):
        self.sign_image.configure(image='')
        image = cv2.imread(file_path)
        
        if image is None:
            messagebox.showerror("Error", "Unable to load image.")
            return

        grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.facec.detectMultiScale(grey_image, scaleFactor=1.3, minNeighbors=5)

        try:
            for (x, y, w, h) in faces:
                fc = grey_image[y:y+h, x:x+w]
                roi = cv2.resize(fc, (48, 48))
                pred = self.EMOTION_LIST[np.argmax(self.model.predict(roi[np.newaxis, :, :, np.newaxis]))]
                self.label1.configure(foreground="#011638", text=pred)
        except Exception as e:
            self.label1.configure(foreground="#011638", text="Unable to Detect: " + str(e))

    def show_Detect_button(self, file_path):
        detect_b = Button(self, text="Detect Emotion", command=lambda: self.Detect(file_path), padx=10, pady=5)
        detect_b.configure(background="#361456", foreground='white', font=('arial', 10, 'bold'))
        detect_b.place(relx=0.79, rely=0.46)

    def upload_image(self):
        try:
            file_path = filedialog.askopenfilename()
            uploaded = Image.open(file_path)
            uploaded.thumbnail((self.controller.winfo_width()/2.3, self.controller.winfo_height()/2.3))
            im = ImageTk.PhotoImage(uploaded)

            self.sign_image.configure(image=im)
            self.sign_image.image = im
            self.label1.configure(text='')

            self.show_Detect_button(file_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload image: {str(e)}")
##################################################################################################################

# Global variables
DATABASE_FILE = "Database.txt"
users = {

}

# Login and Signup Page
class LoginSignupPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        # Create the form heading
        heading = tk.Label(self, text="REGISTRATION FORM", font=("Arial", 20))
        heading.pack(pady=20)

        top_frame = tk.Frame(self, bg='#CDCDCD')
        top_frame.pack(fill='x', pady=10, padx=10)

        # Spacer to push buttons to the right
        spacer = tk.Frame(top_frame, bg='#CDCDCD')
        spacer.pack(side='left', expand=True)

        # Login and Signup buttons aligned to the right
        login_button = tk.Button(top_frame, text="Login", command=self.login)
        signup_button = tk.Button(top_frame, text="Signup", command=self.signup)
        login_button.pack(side='right', padx=5)
        signup_button.pack(side='right', padx=5)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        # Name label and entry
        name_label = tk.Label(form_frame, text="Enter your Full Name:")
        name_label.grid(row=0, column=0, sticky="w", padx=20, pady=5)
        self.name_entry = tk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=20, pady=5)

        # Email label and entry
        email_label = tk.Label(form_frame, text="Enter your email address:")
        email_label.grid(row=1, column=0, sticky="w", padx=20, pady=5)
        self.email_entry = tk.Entry(form_frame, width=30)
        self.email_entry.grid(row=1, column=1, padx=20, pady=5)

        # Verify Email button
        verify_button = tk.Button(form_frame, text="Verify Email Address", command=self.request_otp)
        verify_button.grid(row=1, column=2, padx=10)

        # Password label and entry
        password_label = tk.Label(form_frame, text="Enter your Password:")
        password_label.grid(row=2, column=0, sticky="w", padx=20, pady=5)
        self.password_entry = tk.Entry(form_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=20, pady=5)

        # OTP label and entry
        otp_label = tk.Label(form_frame, text="Enter your OTP:")
        otp_label.grid(row=3, column=0, sticky="w", padx=20, pady=5)
        self.otp_entry = tk.Entry(form_frame, width=30)
        self.otp_entry.grid(row=3, column=1, padx=20, pady=5)

        # Address label and entry
        address_label = tk.Label(form_frame, text="Enter your Address:")
        address_label.grid(row=4, column=0, sticky="w", padx=20, pady=5)
        self.address_entry = tk.Entry(form_frame, width=30)
        self.address_entry.grid(row=4, column=1, padx=20, pady=5)

        # Frame for buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        submit_button = tk.Button(button_frame, text="Submit", command=self.submit)
        submit_button.pack(side="right", padx=10)

        # Add navbar
        self.create_navbar()

    def create_navbar(self):
        # Create navbar frame
        navbar_frame = tk.Frame(self, bg='#CDCDCD')
        navbar_frame.pack(fill='x', pady=10, padx=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=self.controller.navigate_back)
        back_button.pack(side='left', padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=self.controller.navigate_next)
        next_button.pack(side='right', padx=20)


       

        
    
    def request_otp(self):
        email = self.email_entry.get()
        if email:
            otp = self.generate_otp()
            self.send_otp_email(email, otp)
        else:
            messagebox.showerror("Error", "Please enter your email")

    def generate_otp(self, length=6):
        digits = "0123456789"
        return ''.join(random.choice(digits) for i in range(length))

    def send_otp_email(self, email, otp):
        sender_email = "shukla20priyanka@gmail.com"  # Update with your email
        password = "vzsa hidh focw rlph"  # Update with your password

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Your OTP"

        body = f"Your OTP is: {otp}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
            messagebox.showinfo("Success", "OTP sent successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send OTP: {str(e)}")

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if email and password:
            self.load_users()  # Ensure users dictionary is up to date
            print("Loaded users:", users)  # Print loaded users for debugging
            if email in users:
                if users[email]["password"] == password:
                    otp = users[email]["otp"]
                    hidden_password = '*' * len(password)  
                    messagebox.showinfo("Login Details", f"Email: {email}\nPassword: {hidden_password}\nOTP: {otp}")
                else:
                    messagebox.showerror("Error", "Invalid password")
            else:
                messagebox.showerror("Error", "User not found. Please register first.")
        else:
            messagebox.showerror("Error", "Please enter email and password")

            messagebox.showinfo("Info", f"Login with {email}, {password}")

    def signup(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if email and password:
            if email in users:
                 messagebox.showerror("Error", "Email already exists")
            else:
                users[email] = {"password": password, "otp": ""}
                self.save_users()  # Save new user to file
                messagebox.showinfo("Success", "Signup Successful")
        else:
            messagebox.showerror("Error", "Please enter email and password")
            messagebox.showinfo("Info", f"Signup with {email}, {password}")
    
    def load_users():
        global users
        users = {}
        try:
            with open(DATABASE_FILE, 'r') as file:
                for line in file:
                    print("Reading line:", line.strip())  # Debug print
                    parts = line.strip().split(", ")  # Split by comma and space
                    if len(parts) == 3:
                        email = parts[0].split(":")[1].strip()
                        password = parts[1].split(":")[1].strip()
                        address = parts[2].split(":")[1].strip()
                        users[email] = {"password": password, "address": address, "otp": ""}  # Add email, password, and address to users dictionary
                    else:
                        print(f"Ignoring line: {line.strip()} (Format doesn't match)")
        except FileNotFoundError:
            pass  # Return an empty dictionary if the file doesn't exist
        return users


    def save_users():
        with open(DATABASE_FILE, 'w') as file:
            for email, data in users.items():
                file.write(f"{email}:{data['password']}:{data['otp']}\n")

    load_users()



    def submit(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        address = self.address_entry.get()

        if name and email and password and address:
            if email in users:
                messagebox.showerror("Error", "Email already exists")
            else:
                try:
                    with open(DATABASE_FILE, 'a') as file:
                        file.write(f"Name: {name}, Email: {email}, Password: {password}, Address: {address}\n")
                        users[email] = {"password": password, "otp": ""}
                        messagebox.showinfo("Success", "Details submitted successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to submit details: {str(e)}")
        else:
            messagebox.showerror("Error", "Please fill in all fields")

#####################################################################################################################
# Delivery Address Page
class DeliveryAddressPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        canvas = tk.Canvas(self, bg="white", width=600, height=420)
        canvas.place(x=50, y=20)
        canvas.pack()

        heading_text = "Fill Address"
        canvas.create_text(350, 40, text=heading_text, font=("Helvetica", 20), fill="blue")

        # Current Address Label and Entry
        current_address_label = tk.Label(canvas, text="Current Address:", padx=10, pady=5)
        canvas.create_window(100, 90, window=current_address_label)
        self.current_address_entry = tk.Entry(canvas, width=50)
        canvas.create_window(350, 90, window=self.current_address_entry)

        # Delivery Address Label and Entry
        delivery_address_label = tk.Label(canvas, text="Delivery Address:", padx=10, pady=5)
        canvas.create_window(100, 140, window=delivery_address_label)
        self.delivery_address_entry = tk.Entry(canvas, width=50)
        canvas.create_window(350, 140, window=self.delivery_address_entry)

        # Button to fill delivery address
        button = tk.Button(self, text="Fill Delivery Address", command=self.fill_delivery_address)
        canvas.create_window(350, 190, window=button)
        
        # Add navbar
        self.create_navbar()

    def create_navbar(self):
        # Create navbar frame
        navbar_frame = tk.Frame(self, bg='#CDCDCD')
        navbar_frame.pack(fill='x', pady=10, padx=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=self.controller.navigate_back)
        back_button.pack(side='left', padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=self.controller.navigate_next)
        next_button.pack(side='right', padx=20)
        
       # Set the current address in the entry widget
        self.current_address_entry.insert(0, self.get_current_address())

    def get_current_address(self):
        try:
            # For demonstration, using hardcoded coordinates
            latitude = 26.4789045
            longitude = 80.388953

            geolocator = Nominatim(user_agent="your_app_name")
            location = geolocator.reverse((latitude, longitude))
            return location.address
        except GeocoderInsufficientPrivileges as e:
            return f"Error: {e}"

    def fill_delivery_address(self):
        current_address = self.get_current_address()
        self.delivery_address_entry.delete(0, tk.END)
        self.delivery_address_entry.insert(0, current_address)
####################################################################################################################
# Function to get current time in IST
def get_current_time():
    tz = pytz.timezone('Asia/Kolkata')  # IST timezone
    return datetime.now(tz)

# Function to get current city and state using IP address
def get_current_city_state():
    try:
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.geocode('')
        if location:
            address_components = location.address.split(', ')
            if len(address_components) >= 3:
                city_state = address_components[-3:-1]  # Assuming this returns city, state
                return city_state
            else:
                return ["Unnao", "Uttar Pradesh"]  # Default to Unnao, Uttar Pradesh
        else:
            return ["Unnao", "Uttar Pradesh"]  # Default to Unnao, Uttar Pradesh
    except Exception as e:
        print(f"Error fetching city/state: {e}")
        return ["Unnao", "Uttar Pradesh"]  # Default to Unnao, Uttar Pradesh

# Function to get weather data from OpenWeatherMap API
def get_weather(lat, lon):
    api_key = 'be592c0049dfe6c1c6b7239aa6dff774'  # Replace with your actual API key
    base_url = f'https://api.openweathermap.org/data/2.5/weather?'
    url = f'{base_url}lat={lat}&lon={lon}&appid={api_key}&units=metric'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)

        data = response.json()

        temperature = data['main']['temp']
        country = data['sys']['country']
        city = data['name'] 

        return temperature, country, city

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None, None, None

# Function to change app theme based on daytime
def change_theme(is_daytime, app):
    if is_daytime:
        app.config(bg='white')  # Light theme
    else:
        app.config(bg='black')  # Dark theme

    
# Weather Page
class WeatherPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(bg='lightblue')
        
        # Header
        header_label = tk.Label(self, text="Weather and Address Information", font=("Arial", 18), bg='lightblue')
        header_label.pack(pady=20)

        # Current Address Label and Entry
        self.current_address_label = tk.Label(self, text="Current Address: ", font=("Arial", 12), bg='lightblue')
        self.current_address_label.pack(pady=5)
        self.current_address_value = tk.Label(self, text="", font=("Arial", 12), bg='lightblue')
        self.current_address_value.pack(pady=5)

        # Delivery Address Label and Entry
        self.delivery_address_label = tk.Label(self, text="Delivery Address: ", font=("Arial", 12), bg='lightblue')
        self.delivery_address_label.pack(pady=5)
        self.delivery_address_value = tk.Label(self, text="", font=("Arial", 12), bg='lightblue')
        self.delivery_address_value.pack(pady=5)

        # Weather Information
        self.temperature_label = tk.Label(self, text="Temperature: ", font=("Arial", 12), bg='lightblue')
        self.temperature_label.pack(pady=5)
        self.city_label = tk.Label(self, text="City: ", font=("Arial", 12), bg='lightblue')
        self.city_label.pack(pady=5)
        self.country_label = tk.Label(self, text="Country: ", font=("Arial", 12), bg='lightblue')
        self.country_label.pack(pady=5)

        # Load and display data
        self.update_information()

         # Add navbar
        self.create_navbar()

    def create_navbar(self):
        # Create navbar frame
        navbar_frame = tk.Frame(self, bg='#CDCDCD')
        navbar_frame.pack(fill='x', pady=10, padx=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=self.controller.navigate_back)
        back_button.pack(side='left', padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=self.controller.navigate_next)
        next_button.pack(side='right', padx=20)

    def update_information(self):
        current_time = get_current_time()  # Call the standalone function directly
        if current_time.hour >= 6 and current_time.hour < 12:
            city_state = get_current_city_state()
            if city_state:
                city, state = city_state
                self.current_address_value.config(text=f"{city}, {state}")
                self.delivery_address_value.config(text=f"{city}, {state}")
                change_theme(True, self)  # Light theme
            else:
                city = "Unnao"  # Default city setting
                self.current_address_value.config(text=city)
                self.delivery_address_value.config(text=city)
        else:
            lat, lon = 26.5673264, 80.61981926788883  # Replace with actual logic to fetch coordinates based on time
            temperature, country, city = get_weather(lat, lon)
            if temperature is not None and country is not None and city is not None:
                self.current_address_value.config(text=f"{city}")
                self.delivery_address_value.config(text=f"{city}")
                self.temperature_label.config(text=f"Temperature: {temperature}°C")
                self.city_label.config(text=f"City: {city}")
                self.country_label.config(text=f"Country: {country}")
                change_theme(False, self)  # Dark theme
            else:
                self.current_address_value.config(text="Unnao")
                self.delivery_address_value.config(text="Unnao")
##########################################################################################################################
# Coupon Page
class CouponPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up UI components
        self.label_total_price = tk.Label(self, text="Total Price:")
        self.entry_total_price = tk.Entry(self)
        self.label_coupon_code = tk.Label(self, text="Coupon Code:")
        self.entry_coupon_code = tk.Entry(self)
        self.label_discounted_price = tk.Label(self, text="Discounted Price: 0.00")
        self.label_discount_percentage = tk.Label(self, text="Discount Applied: 0%")

        # Heading
        heading = tk.Label(self, text="Coupon Code Application", pady=20, font=('arial', 25, 'bold'))
        heading.configure(background="#CDCDCD", foreground="#364156")
        heading.pack()

        # Layout
        self.label_total_price.pack(pady=10)
        self.entry_total_price.pack(pady=5)
        self.label_coupon_code.pack(pady=10)
        self.entry_coupon_code.pack(pady=5)

        button_generate_coupon = tk.Button(self, text="Generate Coupon Code", command=self.on_generate_coupon)
        button_generate_coupon.pack(pady=10)

        button_apply_coupon = tk.Button(self, text="Apply Coupon", command=self.on_apply_coupon)
        button_apply_coupon.pack(pady=10)

        self.label_discounted_price.pack(pady=10)
        self.label_discount_percentage.pack(pady=10)
        
        # Add navbar
        self.create_navbar()

    def create_navbar(self):
        # Create navbar frame
        navbar_frame = tk.Frame(self, bg='#CDCDCD')
        navbar_frame.pack(fill='x', pady=10, padx=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=self.controller.navigate_back)
        back_button.pack(side='left', padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=self.controller.navigate_next)
        next_button.pack(side='right', padx=20)

    def generate_coupon_code(self):
        """Generate a random 5-digit coupon code."""
        return ''.join([str(random.randint(0, 9)) for _ in range(5)])

    def calculate_discount(self, coupon_code):
        """Calculate the discount based on the coupon code."""
        digit_sum = sum(int(digit) for digit in coupon_code)
        if digit_sum % 2 == 0:
            return 0.15  # 15% discount
        else:
            return 0.10  # 10% discount

    def apply_coupon_code(self, total_price, coupon_code):
        """Apply the coupon code to the total price."""
        discount = self.calculate_discount(coupon_code)
        discounted_price = total_price * (1 - discount)
        return discounted_price, discount * 100  # Return discount percentage

    def on_apply_coupon(self):
        """Event handler for applying the coupon."""
        try:
            total_price = float(self.entry_total_price.get())
            coupon_code = self.entry_coupon_code.get()

            if len(coupon_code) != 5 or not coupon_code.isdigit():
                messagebox.showerror("Invalid Coupon Code", "Please enter a valid 5-digit numeric coupon code.")
                return

            discounted_price, discount_percentage = self.apply_coupon_code(total_price, coupon_code)
            self.label_discounted_price.config(text=f"Discounted Price: {discounted_price:.2f}")
            self.label_discount_percentage.config(text=f"Discount Applied: {discount_percentage:.0f}%")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid total price.")

    def on_generate_coupon(self):
        """Event handler for generating a coupon code."""
        coupon_code = self.generate_coupon_code()
        self.entry_coupon_code.delete(0, tk.END)
        self.entry_coupon_code.insert(0, coupon_code)
#######################################################################################################################
products = [
    # A-E
    "Apple", "Apricot", "Avocado", "Artichoke", "Asparagus",
    "Banana", "Blueberry", "Blackberry", "Broccoli", "Brussels Sprout",
    "Cherry", "Cranberry", "Cantaloupe", "Cucumber", "Carrot",
    "Date", "Dragonfruit", "Durian", "Daikon", "Dill",
    "Eggplant", "Elderberry", "Endive", "Escarole", "Edamame",
    # F-J
    "Fig", "Feijoa", "Fennel", "Fiddlehead", "Finger Lime",
    "Grape", "Gooseberry", "Guava", "Ginger", "Grapefruit",
    "Honeydew", "Huckleberry", "Horseradish", "Hops", "Hibiscus",
    "Indian Fig", "Iceberg Lettuce", "Icaco", "Ilama", "Imbu",
    "Jackfruit", "Jambul", "Jicama", "Jujube", "Jaboticaba",
    # K-O
    "Kiwi", "Kumquat", "Kale", "Kohlrabi", "Kiwano",
    "Lemon", "Lime", "Lychee", "Leek", "Lavender",
    "Mango", "Mulberry", "Melon", "Mushroom", "Mint",
    "Nectarine", "Nutmeg", "Nance", "Navel Orange", "Napa Cabbage",
    "Orange", "Olive", "Onion", "Okra", "Oregano",
    # P-T
    "Pineapple", "Papaya", "Peach", "Pear", "Plum",
    "Quince", "Quinoa", "Quail Egg", "Quandong", "Quararibea",
    "Raspberry", "Rambutan", "Radish", "Raisin", "Rutabaga",
    "Strawberry", "Spinach", "Squash", "Starfruit", "Sage",
    "Tomato", "Tangerine", "Turnip", "Thyme", "Taro",
    # U-Z
    "Ugli Fruit", "Ube", "Udon", "Umbrella Fruit", "Urfa Biber",
    "Vanilla", "Velvet Apple", "Voavanga", "Valencia Orange", "Verdolaga",
    "Watermelon", "Wolfberry", "Walnut", "Wasabi", "Wheatgrass",
    "Xigua", "Ximenia", "Xylocarp", "Xoconostle", "Xerophyte",
    "Yam", "Yuzu", "Yam Bean", "Yarrow", "Yellow Squash",
    "Zucchini", "Ziziphus", "Zereshk", "Zest", "Zostera"
]


class VoiceProductSearchPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        frame = tk.Frame(self)
        frame.pack(pady=20)

        heading_label = tk.Label(frame, text="My Product List", font=("Arial", 24, "bold"))
        heading_label.pack(pady=10)

        search_label = tk.Label(frame, text="Type the product name and press Search:")
        search_label.pack(pady=10)

        self.search_entry = tk.Entry(frame)
        self.search_entry.pack(pady=5)

        search_button = tk.Button(frame, text="Search", command=self.search_products_by_text)
        search_button.pack(pady=10)

        instructions_label = tk.Label(frame, text="Press the button and say product names or upload a voice file.")
        instructions_label.pack(pady=10)

        record_button = tk.Button(frame, text="Record Voice", command=self.start_search_from_recording)
        record_button.pack(pady=10)

        upload_button = tk.Button(frame, text="Upload Voice File", command=self.start_search_from_upload)
        upload_button.pack(pady=10)

        self.result_frame = tk.Frame(frame)
        self.result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Add a navigation button to go back to the home page

         # Add navbar
        self.create_navbar()

    def create_navbar(self):
        # Create navbar frame
        navbar_frame = tk.Frame(self, bg='#CDCDCD')
        navbar_frame.pack(fill='x', pady=10, padx=10)

        back_button = tk.Button(navbar_frame, text="← Back", command=self.controller.navigate_back)
        back_button.pack(side='left', padx=20)

        next_button = tk.Button(navbar_frame, text="Next →", command=self.controller.navigate_next)
        next_button.pack(side='right', padx=20)


     

    def start_search_from_recording(self):
        voice_input = self.record_voice()
        self.display_results(voice_input)

    def start_search_from_upload(self):
        voice_input = self.upload_voice()
        self.display_results(voice_input)

    def search_products_by_text(self):
        text_input = self.search_entry.get().strip().lower()
        if text_input in [product.lower() for product in products]:
            messagebox.showinfo("Success", "Product found")
        else:
            messagebox.showinfo("Unsuccessful", "Product not found in product list")

    def display_results(self, voice_input):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if voice_input:
            results = self.search_products(voice_input, products)
            if results[0] == "Product found":
                messagebox.showinfo("Success", "Product found")
            else:
                status_label = tk.Label(self.result_frame, text=results[0])
                status_label.pack(pady=5)

                columns = [letter.upper() for letter in 'abcde']
                tree = tk.Treeview(self.result_frame, columns=columns, show='headings')
                for col in columns:
                    tree.heading(col, text=col)
                tree.pack(pady=10, fill=tk.BOTH, expand=True)

                column_data = {letter: [] for letter in 'abcde'}
                for product in results[1:]:
                    first_letter = product[0].lower()
                    if first_letter in column_data:
                        column_data[first_letter].append(product)

                max_items = max(len(column_data[letter]) for letter in 'abcde')

                for i in range(max_items):
                    row = []
                    for letter in 'abcde':
                        if i < len(column_data[letter]):
                            row.append(column_data[letter][i])
                        else:
                            row.append("")
                    tree.insert("", tk.END, values=row)
    def record_voice(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something!")
            try:
                audio = r.listen(source, timeout=10)
            except sr.WaitTimeoutError:
                messagebox.showerror("Error", "Listening timed out while waiting for phrase to start")
                return None
        try:
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            messagebox.showerror("Error", f"Could not request results from Google Speech Recognition service; {e}")
            return None

    def upload_voice(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.flac *.mp3")])
        if not file_path:
            return None

        r = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Google Speech Recognition could not understand the audio")
            return None
        except sr.RequestError as e:
            messagebox.showerror("Error", f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except ValueError as e:
            messagebox.showerror("Error", f"Audio file could not be read; check if the file is corrupted or in another format: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return None



if __name__ == "__main__":
    app = MultiPageApp()
    app.mainloop()


