from flask import Flask, render_template, request, session,render_template, request, redirect, session, url_for, jsonify, flash
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime, date, time
import sqlite3
import pandas as pd  # Make sure to include this import
import json  # This import is also used in the login function
import tkinter as tk
from tkinter import messagebox
import base64
from PIL import Image
import io
import csv

name="vikas"
app = Flask(__name__)
app.secret_key = 'vikas' 

# Add these global variables at the top of your file
PUNCH_TYPE = None

# Define shift timings
SHIFTS = {
    'Morning': {
        'start': time(6, 0),  # 6:00 AM
        'end': time(14, 0),   # 2:00 PM
    },
    'Afternoon': {
        'start': time(14, 0), # 2:00 PM
        'end': time(22, 0),   # 10:00 PM
    },
    'Night': {
        'start': time(22, 0), # 10:00 PM
        'end': time(6, 0),    # 6:00 AM
    }
}

# Define the path to credentials file
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'templates', 'cred.csv')

# Function to show alert message
def show_alert():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showinfo("Success", "Image captured successfully! Press ESC to exit camera.")
    root.destroy()

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method=="POST":
        return render_template('index.html')
    else:
        return "Everything is okay!"

@app.route('/name', methods=['GET', 'POST'])
def name():
    if request.method == "POST":
        name1 = request.form['name1']
        ID = request.form['name2']
        Designation = request.form['name3']
        return render_template('camera.html', 
                             name1=name1, 
                             ID=ID, 
                             Designation=Designation,
                             insecure_warning=True)
    else:
        return 'All is not well'

@app.route('/save-photo', methods=['POST'])
def save_photo():
    try:
        image = request.files['image']
        name1 = request.form['name1']
        name2 = request.form['name2']
        name3 = request.form['name3']
        
        # Create the Training images directory if it doesn't exist
        training_dir = 'Training images'
        if not os.path.exists(training_dir):
            os.makedirs(training_dir)
        
        # Save the image with the formatted filename
        filename = f"{name1}.{name2}.{name3}.png"
        filepath = os.path.join(training_dir, filename)
        image.save(filepath)
        
        # Reload the known faces after adding new image
        global encodeListKnown, classNames
        encodeListKnown, classNames = load_known_faces()
        
        return jsonify({
            'success': True,
            'message': 'Photo saved successfully to Training images folder',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route("/", methods=["GET", "POST"])
def recognize():
    if request.method == "POST":
        return render_template('recognize.html')
    else:
        return render_template('main.html')

@app.route('/logout', methods=["POST"])
def logout():
    json_data = json.loads(request.data.decode())
    username = json_data['username']
    
    # Logic to find the row for the user and update the out-time
    with open('attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        updatedDataList = []
        for line in myDataList:
            entry = line.split(',')
            if entry[0] == username:
                entry[4] = datetime.now().strftime('%H:%M')  # Set out-time
            updatedDataList.append(','.join(entry))
        f.seek(0)
        f.writelines(updatedDataList)
        f.truncate()
    
    # Clear the session
    session.pop('username', None)
    
    return 'Out-time recorded successfully'

# @app.route('/login',methods = ['POST'])
# def login():
#     #print( request.headers )
#     json_data = json.loads(request.data.decode())
#     username = json_data['username']
#     password = json_data['password']
#     #print(username,password)
#     df= pd.read_csv('cred.csv')
#     if len(df.loc[df['username'] == username]['password'].values) > 0:
#         if df.loc[df['username'] == username]['password'].values[0] == password:
#             session['username'] = username
#             return 'success'
#         else:
#             return 'failed'
#     else:
#         return 'failed'
        
# @app.route('/login', methods=['POST'])
# def login():
#     json_data = request.form  # Change to request.form
#     username = json_data['username']
#     password = json_data['password']
#     role = json_data['role']  # Get the selected role

#     df = pd.read_csv('C:\\Users\\pravi\\Downloads\\CGE-Attendance-App\\CGE-Attendance-App\\templates\\cred.csv')
    
#     # Check credentials based on role
#     if len(df.loc[df['username'] == username]['password'].values) > 0:
#         if df.loc[df['username'] == username]['password'].values[0] == password:
#             session['username'] = username
#             session['role'] = role  # Store the role in the session
#             return redirect(url_for('emp')) 
#         else:
#             return 'failed'
#     else:
#         return 'Login Failed: User not found'
#     return render_template('main.html')

@app.route('/login', methods=['GET','POST'])
def login():
    try:
        json_data = request.form
        username = json_data['username']
        password = json_data['password']
        role = json_data['role']
        user_id = json_data.get('userid', '')

        # Debug prints
        print("Login attempt:")
        print(f"Username: {username}")
        print(f"UserID: {user_id}")
        print(f"Role: {role}")

        df = pd.read_csv(CREDENTIALS_FILE)
        
        # Debug: Print DataFrame info
        print("\nCredentials file content:")
        print(df.head())
        print("\nColumns:", df.columns.tolist())

        # Convert user_id to string for comparison
        df['userid'] = df['userid'].astype(str)
        user_id = str(user_id)

        # Debug: Print filtered records
        print("\nFiltering for:")
        print(f"Username: {username}, UserID: {user_id}")
        
        user_record = df.loc[
            (df['username'] == username) & 
            (df['userid'] == user_id)
        ]

        print("\nFound records:")
        print(user_record)

        if user_record.empty:
            return render_template('main.html', 
                error="Invalid Login: Username or ID not found")

        # Debug: Print password comparison
        print("\nPassword check:")
        print(f"Input password: {password}")
        print(f"Stored password: {user_record['password'].values[0]}")

        if user_record['password'].values[0] != password:
            return render_template('main.html', 
                error="Invalid Login: Incorrect password")

        # Debug: Print role comparison
        print("\nRole check:")
        print(f"Input role: {role}")
        print(f"Stored role: {user_record['role'].values[0]}")

        if user_record['role'].values[0] != role:
            return render_template('main.html', 
                error="Invalid Login: Role mismatch")

        # If all checks pass, store session and redirect
        session['username'] = username
        session['role'] = role
        session['user_id'] = user_id
        session['designation'] = user_record['designation'].values[0] if 'designation' in user_record else ''
        
        print("\nLogin successful!")
        return redirect(url_for('emp'))
            
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug print
        return render_template('main.html', 
            error=f"System Error: {str(e)}")  # Show actual error for debugging

@app.route('/main')
def main():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('emp.html')  # Render the main page if logged in
@app.route('/emp')
def emp():
    return render_template('emp.html')  # or whatever your intended logic is
# @app.route('/logout')
# def logout():
#     session.pop('username', None)  # Remove the username from the session
#     session.pop('role', None)  # Remove the role from the session
#     return redirect(url_for('login'))  # Redirect to login page

@app.route('/checklogin')
def checklogin():
    #print('here')
    if 'username' in session:
        return session['username']
    return 'False'


@app.route('/how',methods=["GET","POST"])
def how():
    return render_template('form.html')
@app.route('/data',methods=["GET","POST"])
def data():
    '''user=request.form['username']
    pass1=request.form['pass']
    if user=="tech" and pass1=="tech@321" :
    '''
    if request.method=="POST":
        today=date.today()
        print(today)
        conn = sqlite3.connect('information.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        print ("Opened database successfully");
        cursor = cur.execute("SELECT NAME,EmpId,DESIGNATION,Time,Date,Shift  from CGEmployeeData where Date=?",(today,))
        rows=cur.fetchall()
        print(rows)
        for line in cursor:

            data1=list(line)
        print ("Operation done successfully")
        conn.close()

        return render_template('form2.html',rows=rows)
    else:
        return render_template('form1.html')


            
@app.route('/whole',methods=["GET","POST"])
def whole():
    today=date.today()
    print(today)
    conn = sqlite3.connect('information.db')
    conn.row_factory = sqlite3.Row 
    cur = conn.cursor() 
    print ("Opened database successfully")
    cursor = cur.execute("SELECT NAME,EmpId,DESIGNATION,Time,Date,Shift  from CGEmployeeData")
    rows=cur.fetchall()    
    return render_template('form3.html',rows=rows)

@app.route('/dashboard',methods=["GET","POST"])
def dashboard():
    return render_template('dashboard.html')

# Sending Email about the attendance report to the faculties/ parents / etc.
# Not working currently
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

def sendMail():
    mssg=MIMEMultipart()


    server=smtplib.SMTP("smtp.gmail.com",'587')
    server.starttls()
    print("Connected with the server")
    user=input("Enter username:")
    pwd=input("Enter password:")
    server.login(user,pwd)
    print("Login Successful!")
    send=user
    rcv=input("Enter Receiver's Email id:")
    mssg["Subject"] = "Employee Report csv"
    mssg["From"] = user
    mssg["To"] = rcv

    body='''
        <html>
        <body>
         <h1>Employee Quarterly Report</h1>
         <h2>Contains the details of all the employees</h2>
         <p>Do not share confidential information with anyone.</p>
        </body>
        </html>
         '''

    body_part=MIMEText(body,'html')
    mssg.attach(body_part)

    with open("emp.csv",'rb') as f:
        mssg.attach(MIMEApplication(f.read(),Name="emp.csv"))

    server.sendmail(mssg["From"],mssg["To"],mssg.as_string())
   # server.quit()

def load_known_faces():
    known_face_encodings = []
    known_face_details = []
    path = 'Training images'
    
    if not os.path.exists(path):
        return [], []
        
    for img_name in os.listdir(path):
        if img_name.endswith(('.png', '.jpg', '.jpeg')):
            # Extract details from filename
            name, id_num, designation = img_name.rsplit('.', 1)[0].split('.')
            
            # Load and encode face
            image_path = os.path.join(path, img_name)
            face_image = face_recognition.load_image_file(image_path)
            try:
                face_encoding = face_recognition.face_encodings(face_image)[0]
                known_face_encodings.append(face_encoding)
                known_face_details.append((name, id_num, designation))
            except IndexError:
                print(f"No face found in {img_name}")
                continue
            
    return known_face_encodings, known_face_details

# Initialize face encodings when app starts
encodeListKnown, classNames = load_known_faces()

@app.route('/set-punch-type/<type>')
def set_punch_type(type):
    try:
        global PUNCH_TYPE
        if type not in ['in', 'out']:
            return jsonify({'error': 'Invalid punch type'}), 400
        PUNCH_TYPE = type
        return jsonify({'status': 'success', 'type': type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def determine_shift():
    current_time = datetime.now().time()
    
    for shift_name, timing in SHIFTS.items():
        if shift_name == 'Night':
            # Special handling for night shift that crosses midnight
            if current_time >= timing['start'] or current_time < timing['end']:
                return shift_name
        else:
            if timing['start'] <= current_time < timing['end']:
                return shift_name
    
    return 'Unknown'

def validate_punch_in(name, id_num, date):
    try:
        filename = f'Attendance/Attendance-{date}.csv'
        if not os.path.exists(filename):
            return False, "No attendance record found for today"
            
        with open(filename, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 6 and row[0] == name and row[1] == id_num:
                    # Check if punch in exists and is not empty
                    if row[5] and row[5].strip():
                        return True, "Punch in record found"
                    else:
                        return False, "No punch in time recorded"
                        
        return False, "No record found for this employee today"
        
    except Exception as e:
        return False, f"Error validating punch in: {str(e)}"

def markAttendance(name, id_num, designation, punch_type):
    try:
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        current_shift = determine_shift()
        
        if not os.path.exists('Attendance'):
            os.makedirs('Attendance')
            
        filename = f'Attendance/Attendance-{date}.csv'
        headers = ['Name', 'ID', 'Designation', 'Date', 'Shift', 'Punch In', 'Punch Out', 'Status', 
                  'Login Role', 'Login Username', 'Login UserID']  # Added new columns
        
        # Get login details from session
        login_role = session.get('role', 'Unknown')
        login_username = session.get('username', 'Unknown')
        login_userid = session.get('user_id', 'Unknown')
        
        # Create new file with headers if it doesn't exist
        if not os.path.exists(filename):
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        rows = []
        user_found = False
        status_message = ""
        
        try:
            with open(filename, 'r', newline='') as f:
                reader = csv.reader(f)
                file_headers = next(reader, None)
                rows.append(headers)
                
                for row in reader:
                    current_row = list(row)
                    # Extend row if it doesn't have all columns
                    while len(current_row) < len(headers):
                        current_row.append('')
                    
                    if len(current_row) >= 2 and current_row[0] == name and current_row[1] == id_num:
                        user_found = True
                        if punch_type == 'in':
                            if current_row[5] and current_row[5].strip():
                                raise ValueError(f"Already punched in at {current_row[5]}")
                            
                            current_row[4] = current_shift
                            current_row[5] = time
                            current_row[7] = 'Present'
                            # Add login details
                            current_row[8] = login_role
                            current_row[9] = login_username
                            current_row[10] = login_userid
                            status_message = f"Punch In recorded for {name} at {time} ({current_shift} shift)"
                        elif punch_type == 'out':
                            if not current_row[5]:
                                raise ValueError("No punch in record found. Please punch in first.")
                            
                            current_row[6] = time
                            
                            shift_end = SHIFTS[current_row[4]]['end']
                            current_time = datetime.strptime(time, '%H:%M:%S').time()
                            
                            if current_time < shift_end:
                                current_row[7] = 'Early Departure'
                            
                            status_message = f"Punch Out recorded for {name} at {time}"
                    
                    rows.append(current_row)
                
                if not user_found:
                    if punch_type == 'in':
                        new_row = [name, id_num, designation, date, current_shift, time, '', 'Present',
                                 login_role, login_username, login_userid]  # Include login details
                        rows.append(new_row)
                        status_message = f"New Punch In recorded for {name} at {time} ({current_shift} shift)"
                    else:
                        raise ValueError("No punch in record found. Please punch in first.")
        
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            raise
        
        # Write all rows back to file
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        return status_message, current_shift
            
    except Exception as e:
        print(f"Error in markAttendance: {str(e)}")
        raise Exception(str(e))

@app.route('/get-current-shift')
def get_current_shift():
    return jsonify({
        'shift': determine_shift(),
        'time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/process-frame', methods=['POST'])
def process_frame():
    try:
        global PUNCH_TYPE
        if not PUNCH_TYPE:
            return jsonify({'error': 'Please select Punch In or Punch Out first'})
            
        print("Starting face processing...")
        
        if not encodeListKnown or not classNames:
            print("No encoded faces found in database")
            return jsonify({
                'error': 'No faces in database', 
                'encoded_faces': len(encodeListKnown), 
                'known_names': len(classNames)
            })

        if 'image' not in request.files:
            print("No image file received")
            return jsonify({'error': 'No image file'})

        # Load and process the image
        image_file = request.files['image']
        
        # Convert the image to bytes
        image_bytes = image_file.read()
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            print("Failed to decode image")
            return jsonify({'error': 'Failed to decode image'})
            
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        print(f"Image shape: {frame_rgb.shape}")
        
        # Ensure image is 8-bit
        if frame_rgb.dtype != np.uint8:
            frame_rgb = frame_rgb.astype(np.uint8)
        
        # Find faces in the frame
        face_locations = face_recognition.face_locations(frame_rgb)
        print(f"Found {len(face_locations)} faces")
        
        if not face_locations:
            return jsonify({'name': 'No face detected'})
            
        # Get face encodings
        face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
        print(f"Generated {len(face_encodings)} encodings")

        # Process each face found
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(encodeListKnown, face_encoding, tolerance=0.5)
            print(f"Match results: {matches}")
            
            if True in matches:
                match_index = matches.index(True)
                Name, ID, Designation = classNames[match_index]
                
                face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
                confidence = 1 - face_distances[match_index]
                print(f"Match found: {Name} with confidence {confidence}")
                
                if confidence > 0.5:
                    try:
                        status_message, current_shift = markAttendance(Name, ID, Designation, PUNCH_TYPE)
                        
                        return jsonify({
                            'name': Name,
                            'id': ID,
                            'designation': Designation,
                            'confidence': f"{confidence:.2%}",
                            'status': status_message,
                            'shift': current_shift
                        })
                    except Exception as e:
                        return jsonify({
                            'error': str(e)
                        })

        print("No matches found above confidence threshold")
        return jsonify({'name': 'Unknown'})

    except Exception as e:
        print(f"Error in process_frame: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/debug-encodings')
def debug_encodings():
    try:
        # Reload encodings
        global encodeListKnown, classNames
        encodeListKnown, classNames = load_known_faces()
        
        # Get training images info
        path = 'Training images'
        training_images = []
        if os.path.exists(path):
            for img_name in os.listdir(path):
                if img_name.endswith(('.png', '.jpg', '.jpeg')):
                    full_path = os.path.join(path, img_name)
                    size = os.path.getsize(full_path)
                    training_images.append({
                        'name': img_name,
                        'size': size,
                        'path': full_path
                    })
        
        return jsonify({
            'encoded_faces_count': len(encodeListKnown),
            'known_names_count': len(classNames),
            'known_names': classNames,
            'training_images': training_images
        })
    except Exception as e:
        return jsonify({'error': str(e)})

def check_punch_status(name, id_num):
    try:
        date = datetime.now().strftime('%Y-%m-%d')
        filename = f'Attendance/Attendance-{date}.csv'
        
        if not os.path.exists(filename):
            return None
            
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[0] == name and row[1] == id_num:
                    return {
                        'punch_in': row[4] if len(row) > 4 else None,
                        'punch_out': row[5] if len(row) > 5 else None
                    }
        return None
    except Exception as e:
        print(f"Error checking punch status: {str(e)}")
        return None

@app.route('/check-status/<name>/<id_num>')
def get_punch_status(name, id_num):
    status = check_punch_status(name, id_num)
    return jsonify(status if status else {'punch_in': None, 'punch_out': None})

if __name__ == '__main__':
    app.run(debug=True)



