from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Admin, Course, Gallery, ContactMessage
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

# ------------------ Initialize DB & Superuser ------------------
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin", password=generate_password_hash("admin123"))
        db.session.add(admin)
        db.session.commit()

# ------------------ USER ROUTES ------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/course')
def course_page():
    courses = Course.query.all()
    return render_template('course.html', courses=courses)

@app.route('/gallery')
def gallery_page():
    gallery_items = Gallery.query.all()
    return render_template('gallery.html', gallery=gallery_items)

@app.route('/contact', methods=['GET','POST'])
def contact_page():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form.get('email','')
        message = request.form['message']
        msg = ContactMessage(name=name, phone=phone, email=email, message=message)
        db.session.add(msg)
        db.session.commit()
        flash('Message sent successfully!')
        return redirect(url_for('contact_page'))
    return render_template('contact.html')

# ------------------ ADMIN LOGIN ------------------
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Credentials")
    return render_template('login.html')

# ------------------ ADMIN DASHBOARD ------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    courses = Course.query.all()
    gallery_items = Gallery.query.all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_dashboard.html', courses=courses, gallery=gallery_items, messages=messages)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))


# ------------------ ADD COURSE ------------------
@app.route('/admin/add_course', methods=['POST'])
def add_course():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    name = request.form['name']
    description = request.form['description']
    image_file = request.files.get('image')
    filename = None
    if image_file:
        filename = image_file.filename
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    course = Course(name=name, description=description, image=filename)
    db.session.add(course)
    db.session.commit()
    return redirect(url_for('manage_courses'))

# ------------------ DELETE COURSE ------------------
@app.route('/admin/delete_course/<int:course_id>')
def delete_course(course_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    course = Course.query.get(course_id)
    if course:
        if course.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], course.image))
            except:
                pass
        db.session.delete(course)
        db.session.commit()
    return redirect(url_for('manage_courses'))

# ------------------ EDIT COURSE ------------------
@app.route('/admin/edit_course/<int:course_id>', methods=['GET','POST'])
def edit_course(course_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    course = Course.query.get(course_id)
    if request.method=='POST':
        course.name = request.form['name']
        course.description = request.form['description']
        image_file = request.files.get('image')
        if image_file:
            filename = image_file.filename
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            course.image = filename
        db.session.commit()
        return redirect(url_for('manage_courses'))
    return render_template('edit_course.html', course=course)

# ------------------ ADD GALLERY ------------------
@app.route('/admin/add_gallery', methods=['POST'])
def add_gallery():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    file = request.files['file']
    description = request.form.get('description','')
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_type = 'image' if 'image' in file.mimetype else 'video'
        gallery_item = Gallery(file_name=filename, file_type=file_type, description=description)
        db.session.add(gallery_item)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# ------------------ DELETE GALLERY ITEM ------------------
@app.route('/admin/delete_gallery/<int:item_id>')
def delete_gallery(item_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    item = Gallery.query.get(item_id)
    if item:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.file_name))
        except:
            pass
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('manage_gallery'))

# ------------------ EDIT GALLERY ITEM ------------------
@app.route('/admin/edit_gallery/<int:item_id>', methods=['GET','POST'])
def edit_gallery(item_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    item = Gallery.query.get(item_id)
    if request.method=='POST':
        item.description = request.form.get('description','')
        file = request.files.get('file')
        if file:
            # Delete old file
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.file_name))
            except:
                pass
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            item.file_name = filename
            item.file_type = 'image' if 'image' in file.mimetype else 'video'
        db.session.commit()
        return redirect(url_for('manage_gallery'))
    return render_template('edit_gallery.html', item=item)


from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
from models import db, Course, Gallery, ContactMessage

# ---------------- ADMIN MANAGE COURSES PAGE ----------------
@app.route('/admin/manage_courses', methods=['GET', 'POST'])
def manage_courses():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # form data
        name = request.form['name']
        description = request.form['description']
        image_file = request.files.get('image')

        # save image if uploaded
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join('static/uploads', filename))

        # create new course
        new_course = Course(name=name, description=description, image=filename)
        db.session.add(new_course)
        db.session.commit()

        flash('Course added successfully!', 'success')
        return redirect(url_for('manage_courses'))  # same page reload

    courses = Course.query.all()
    return render_template('manage_courses.html', courses=courses)

# ---------------- ADMIN MANAGE GALLERY PAGE ----------------
# ---------------- ADMIN MANAGE GALLERY PAGE ----------------
@app.route('/admin/manage_gallery', methods=['GET', 'POST'])
def manage_gallery():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')
        filename = None
        file_type = None

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))

            # Determine file type
            if file.content_type.startswith('image'):
                file_type = 'image'
            elif file.content_type.startswith('video'):
                file_type = 'video'

            new_item = Gallery(file_name=filename, file_type=file_type, description=description)
            db.session.add(new_item)
            db.session.commit()

            flash('Gallery item added successfully!', 'success')
            return redirect(url_for('manage_gallery'))  # SAME page reload

    gallery = Gallery.query.all()
    return render_template('manage_gallery.html', gallery=gallery)

# ---------------- ADMIN CONTACT MESSAGES PAGE ----------------
@app.route('/admin/contact_messages')
def contact_messages():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('contact_messages.html', messages=messages)

# ------------------ RUN APP ------------------
if __name__ == '__main__':
    app.run(debug=True)
