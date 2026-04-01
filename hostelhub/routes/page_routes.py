from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from models import db, Room, Complaint, User, Fee, Notice, Notification, Letter
from sqlalchemy import or_
import datetime
import csv
import io

page_bp = Blueprint('page', __name__)


def create_notification(user_id, title, message, type='info'):
    try:
        new_notif = Notification(userId=user_id, title=title, message=message, type=type)
        db.session.add(new_notif)
        db.session.commit()
    except Exception as e:
        print(f"Error creating notification: {e}")
        db.session.rollback()

def check_and_escalate_complaints():
    two_days_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
    idle_complaints = Complaint.query.filter(
        Complaint.status == 'Pending',
        Complaint.created_at <= two_days_ago,
        Complaint.is_escalated == False
    ).all()
    
    if idle_complaints:
        committee_members = User.query.filter_by(is_committee=True).all()
        for c in idle_complaints:
            c.is_escalated = True
            for cm in committee_members:
                create_notification(cm.id, "Complaint Escalated", f"Complaint '{c.title}' has been auto-escalated to the committee.", "warning")
        db.session.commit()

@page_bp.route('/')
@login_required
def index():
    if current_user.role == 'student':
        return redirect(url_for('page.student_dashboard'))
    return redirect(url_for('page.dashboard'))

@page_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access to admin dashboard.', 'danger')
        return redirect(url_for('page.student_dashboard'))
        
    check_and_escalate_complaints()
        
    total_rooms = Room.query.count()
    total_students = User.query.filter_by(role='student').count()
    active_complaints = Complaint.query.filter_by(status='Pending').count()
    
    return render_template('dashboard.html', 
                         active_page='dashboard',
                         total_rooms=total_rooms,
                         total_students=total_students,
                         active_complaints=active_complaints)

@page_bp.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('page.dashboard'))
        
    my_complaints_count = Complaint.query.filter_by(userId=current_user.id).count()
    pending_fees = Fee.query.filter_by(userId=current_user.id, status='Pending').count()
    
    room_info = None
    if current_user.roomId:
        room_info = Room.query.get(current_user.roomId)
        
    recent_notices = Notice.query.order_by(Notice.created_at.desc()).limit(3).all()
        
    return render_template('student_dashboard.html',
                           active_page='dashboard',
                           my_complaints_count=my_complaints_count,
                           pending_fees=pending_fees,
                           room_info=room_info,
                           recent_notices=recent_notices)

@page_bp.route('/rooms')
@login_required
def rooms():
    all_rooms = Room.query.order_by(Room.roomNumber).all()
    return render_template('rooms.html', active_page='rooms', rooms=all_rooms)

@page_bp.route('/rooms/add', methods=['POST'])
@login_required
def add_room():
    try:
        room_number = request.form.get('roomNumber')
        floor = request.form.get('floor')
        capacity = request.form.get('capacity')
        room_type = request.form.get('type')
        price = request.form.get('price')
        
        if Room.query.filter_by(roomNumber=room_number).first():
            flash(f'Room {room_number} already exists!', 'danger')
            return redirect(url_for('page.rooms'))
            
        new_room = Room(
            roomNumber=room_number,
            floor=int(floor),
            capacity=int(capacity),
            type=room_type,
            price=float(price)
        )
        
        db.session.add(new_room)
        db.session.commit()
        
        flash(f'Room {room_number} added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding room: {str(e)}', 'danger')
        
    return redirect(url_for('page.rooms'))

@page_bp.route('/rooms/delete/<id>')
@login_required
def delete_room(id):
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.rooms'))
        
    room = Room.query.get(id)
    if room:
        if room.occupants:
            flash(f'Cannot delete room {room.roomNumber} as it has occupants.', 'danger')
        else:
            db.session.delete(room)
            db.session.commit()
            flash(f'Room {room.roomNumber} deleted successfully.', 'success')
    else:
        flash('Room not found.', 'danger')
        
    return redirect(url_for('page.rooms'))

@page_bp.route('/complaints')
@login_required
def complaints():
    check_and_escalate_complaints()
    if current_user.role == 'admin':
        all_complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    elif current_user.is_committee:
        all_complaints = Complaint.query.filter(
            or_(Complaint.userId == current_user.id, Complaint.is_escalated == True)
        ).order_by(Complaint.created_at.desc()).all()
    else:
        all_complaints = Complaint.query.filter_by(userId=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template('complaints.html', active_page='complaints', complaints=all_complaints)

@page_bp.route('/complaints/add', methods=['POST'])
@login_required
def add_complaint():
    try:
        category = request.form.get('category')
        room_number = request.form.get('roomNumber') # Used for title
        description = request.form.get('description')
        title = f"{category} issue in {room_number}"
        
        new_complaint = Complaint(
            userId=current_user.id,
            title=title,
            description=description,
            category=category,
            status='Pending'
        )
        
        db.session.add(new_complaint)
        db.session.commit()
        
        # Notify admins
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(admin.id, "New Complaint", f"A new complaint has been filed by {current_user.name}", "warning")
            
        flash('Complaint submitted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting complaint: {str(e)}', 'danger')
        
    return redirect(url_for('page.complaints'))

@page_bp.route('/complaints/update-status/<id>/<status>')
@login_required
def update_complaint_status(id, status):
    if current_user.role != 'admin' and not current_user.is_committee:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.complaints'))
        
    complaint = Complaint.query.get(id)
    if not complaint:
        flash('Complaint not found', 'danger')
        return redirect(url_for('page.complaints'))

    if current_user.is_committee and current_user.role != 'admin':
        if not complaint.is_escalated:
            flash('Unauthorized action', 'danger')
            return redirect(url_for('page.complaints'))

    formatted_status = 'Resolved' if status.lower() == 'resolved' else 'Rejected'
    
    if current_user.role == 'admin' and formatted_status == 'Rejected':
        complaint.is_escalated = True

    complaint.status = formatted_status
    complaint.resolvedById = current_user.id
    db.session.commit()
    
    create_notification(complaint.userId, "Complaint Updated", f"Your complaint '{complaint.title}' has been marked as {formatted_status}", "success" if formatted_status == 'Resolved' else "warning")
    
    flash(f'Complaint marked as {formatted_status}', 'success')

    return redirect(url_for('page.complaints'))

@page_bp.route('/fees')
@login_required
def fees():
    all_fees = Fee.query.order_by(Fee.created_at.desc()).all()
    all_students = User.query.filter_by(role='student').order_by(User.name).all()
    
    total_collected = db.session.query(db.func.sum(Fee.amount)).filter(Fee.status == 'Paid').scalar() or 0
    total_pending = db.session.query(db.func.sum(Fee.amount)).filter(Fee.status != 'Paid').scalar() or 0
    students_owing = Fee.query.filter(Fee.status != 'Paid').group_by(Fee.userId).count()
    
    return render_template('fees.html', 
                         active_page='fees', 
                         fees=all_fees, 
                         students=all_students,
                         total_collected=total_collected,
                         total_pending=total_pending,
                         students_owing=students_owing)

@page_bp.route('/fees/add', methods=['POST'])
@login_required
def add_fee():
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.fees'))
        
    try:
        user_id = request.form.get('studentId')
        amount = request.form.get('amount')
        due_date_str = request.form.get('dueDate')
        description = request.form.get('description')
        status = request.form.get('status', 'Pending')
        
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')
        
        new_fee = Fee(
            userId=user_id,
            amount=float(amount),
            dueDate=due_date,
            semester='AY 2023-24',
            type='Hostel Fee',
            status=status
        )
        
        db.session.add(new_fee)
        db.session.commit()
        
        flash('Fee record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding fee: {str(e)}', 'danger')
        
    return redirect(url_for('page.fees'))

@page_bp.route('/fees/mark-paid/<id>')
@login_required
def mark_fee_paid(id):
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.fees'))
        
    fee = Fee.query.get(id)
    if fee:
        fee.status = 'Paid'
        fee.paymentDate = datetime.datetime.utcnow()
        db.session.commit()
        flash('Fee marked as paid', 'success')
    else:
        flash('Fee record not found', 'danger')
        
    return redirect(url_for('page.fees'))

@page_bp.route('/notice')
@login_required
def notice():
    urgent_notice = Notice.query.filter_by(category='Urgent').order_by(Notice.created_at.desc()).first()
    regular_notices = Notice.query.filter(Notice.category != 'Urgent').order_by(Notice.created_at.desc()).all()
    
    return render_template('notice.html', 
                         active_page='notice', 
                         urgent=urgent_notice, 
                         notices=regular_notices)

@page_bp.route('/notice/add', methods=['POST'])
@login_required
def add_notice():
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.notice'))
        
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        expires_at_str = request.form.get('expiresAt')
        
        expires_at = None
        if expires_at_str:
            expires_at = datetime.datetime.strptime(expires_at_str, '%Y-%m-%d')
            
        new_notice = Notice(
            title=title,
            content=content,
            category=category,
            createdById=current_user.id,
            expiresAt=expires_at
        )
        
        db.session.add(new_notice)
        db.session.commit()
        
        # Notify all students
        students = User.query.filter_by(role='student').all()
        for student in students:
            create_notification(student.id, "New Notice", f"A new notice has been posted: {title}", "info")
            
        flash('Notice posted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error posting notice: {str(e)}', 'danger')
        
    return redirect(url_for('page.notice'))

@page_bp.route('/students')
@login_required
def students():
    all_students = User.query.filter_by(role='student').order_by(User.name).all()
    return render_template('students.html', active_page='students', students=all_students)

@page_bp.route('/students/toggle-committee/<id>')
@login_required
def toggle_committee(id):
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.students'))
        
    student = User.query.get(id)
    if student:
        student.is_committee = not student.is_committee
        db.session.commit()
        status = "added to" if student.is_committee else "removed from"
        flash(f'{student.name} was {status} the Committee.', 'success')
    return redirect(url_for('page.students'))

@page_bp.route('/students/add', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.students'))
        
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        enrollment = request.form.get('enrollment')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('page.students'))
            
        new_student = User(
            name=name,
            email=email,
            role='student',
            enrollmentNumber=enrollment,
            phone=phone
        )
        new_student.set_password(password)
        
        db.session.add(new_student)
        db.session.commit()
        
        flash(f'Student {name} registered successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error registering student: {str(e)}', 'danger')
        
    return redirect(url_for('page.students'))

@page_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name')
            current_user.phone = request.form.get('phone')
            current_user.enrollmentNumber = request.form.get('enrollment')
            current_user.purpose = request.form.get('purpose')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            
    return render_template('profile.html', active_page='profile')

@page_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password:
                if new_password == confirm_password:
                    current_user.set_password(new_password)
                    db.session.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Passwords do not match!', 'danger')
            
            # Purpose can also be set in settings
            purpose = request.form.get('purpose')
            if purpose:
                current_user.purpose = purpose
                db.session.commit()
                flash('Settings updated!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
            
    return render_template('settings.html', active_page='settings')

@page_bp.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(userId=current_user.id).order_by(Notification.created_at.desc()).all()
    # Mark as read
    for n in user_notifications:
        n.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', active_page='notifications', notifications=user_notifications)

@page_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    results = {
        'students': [],
        'rooms': [],
        'notices': []
    }
    
    if query:
        results['students'] = User.query.filter(User.role == 'student', User.name.ilike(f'%{query}%')).all()
        results['rooms'] = Room.query.filter(Room.roomNumber.ilike(f'%{query}%')).all()
        results['notices'] = Notice.query.filter(Notice.title.ilike(f'%{query}%')).all()
        
    return render_template('search_results.html', query=query, results=results)

@page_bp.route('/help')
@login_required
def help_center():
    return render_template('help.html', active_page='help')

@page_bp.route('/letters')
@login_required
def letters():
    if current_user.role == 'admin':
        all_letters = Letter.query.order_by(Letter.created_at.desc()).all()
    else:
        all_letters = Letter.query.filter_by(userId=current_user.id).order_by(Letter.created_at.desc()).all()

    total = len(all_letters)
    pending = sum(1 for l in all_letters if l.status == 'Pending')
    approved = sum(1 for l in all_letters if l.status == 'Approved')
    rejected = sum(1 for l in all_letters if l.status == 'Rejected')

    return render_template('letters.html',
                           active_page='letters',
                           letters=all_letters,
                           total=total,
                           pending=pending,
                           approved=approved,
                           rejected=rejected)


@page_bp.route('/letters/submit', methods=['POST'])
@login_required
def submit_letter():
    try:
        subject = request.form.get('subject')
        category = request.form.get('category')
        body = request.form.get('body')

        new_letter = Letter(
            userId=current_user.id,
            subject=subject,
            category=category,
            body=body,
            status='Pending'
        )
        db.session.add(new_letter)
        db.session.commit()

        # Notify all admins
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(admin.id, "New Letter Received",
                                f"{current_user.name} submitted a letter: {subject}", "info")

        flash('Letter submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting letter: {str(e)}', 'danger')

    return redirect(url_for('page.letters'))


@page_bp.route('/letters/update-status/<id>/<status>', methods=['GET', 'POST'])
@login_required
def update_letter_status(id, status):
    if current_user.role != 'admin':
        flash('Unauthorized action', 'danger')
        return redirect(url_for('page.letters'))

    letter = Letter.query.get(id)
    if letter:
        formatted_status = 'Approved' if status.lower() == 'approved' else 'Rejected'
        letter.status = formatted_status
        letter.reviewedById = current_user.id
        letter.adminRemarks = request.form.get('adminRemarks', '')
        db.session.commit()

        notif_type = 'success' if formatted_status == 'Approved' else 'warning'
        create_notification(letter.userId, "Letter Status Updated",
                            f"Your letter '{letter.subject}' has been {formatted_status}.", notif_type)

        flash(f'Letter {formatted_status}.', 'success')
    else:
        flash('Letter not found.', 'danger')

    return redirect(url_for('page.letters'))


@page_bp.route('/export/<type>')
@login_required
def export_data(type):
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('page.dashboard'))
        
    si = io.StringIO()
    cw = csv.writer(si)
    
    filename = f"{type}_export_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
    
    if type == 'fees':
        fees = Fee.query.all()
        cw.writerow(['ID', 'Semester', 'Amount', 'Type', 'Status', 'Due Date', 'Student ID'])
        for f in fees:
            cw.writerow([f.id, f.semester, f.amount, f.type, f.status, f.dueDate, f.userId])
    elif type == 'complaints':
        complaints = Complaint.query.all()
        cw.writerow(['ID', 'Title', 'Category', 'Status', 'Created At', 'Student ID'])
        for c in complaints:
            cw.writerow([c.id, c.title, c.category, c.status, c.created_at, c.userId])
    else:
        flash('Invalid export type', 'danger')
        return redirect(url_for('page.dashboard'))
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output


