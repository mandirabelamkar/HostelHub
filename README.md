# HostelHub 🏠

A Flask-based hostel management system for managing rooms, students, complaints, fees, notices, and letters.

## Features ✨

- User authentication with role-based access (Student, Admin, Committee)
- Room management and student assignments
- Complaint tracking with escalation support
- Fee management (Hostel, Mess, Fine)
- Notice board with categories
- Letter/request system (Leave, Clearance, Bonafide, Room Change)
- Notification system
- UUID-based database with timestamps

## Tech Stack 🛠️

- Flask 3.0.2
- SQLAlchemy 3.1.1 (ORM)
- MySQL / SQLite
- Flask-Login, Flask-WTF
- PyMySQL, python-dotenv

## Quick Start 🚀

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/hostelhub.git
cd hostelhub
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
SECRET_KEY=your-secret-key
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=your_password
DB_NAME=hostelhub
```

### 3. Initialize & Run
```bash
python init_db.py
python app.py
```

Visit: `http://localhost:5000`

**Default Login:**
- Email: `admin@hostelhub.com`
- Password: `admin123`

## Database Models 🗄️

| Model | Purpose |
|-------|---------|
| User | Students & admins with roles |
| Room | Hostel rooms with capacity & pricing |
| Complaint | Issue tracking with status |
| Notice | Announcements & notices |
| Notification | User notifications |
| Fee | Hostel & mess fee tracking |
| Letter | Student requests (leave, clearance, etc.) |

## Project Structure 📁

```
hostelhub/
├── app.py              # Flask app factory
├── config.py           # Configuration
├── models.py           # Database models
├── init_db.py          # Initialize DB with sample data
├── migrate_temp.py     # Database migrations
└── requirements.txt    # Dependencies
```

## Common Issues 🐛

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| MySQL connection error | Check `.env` credentials & MySQL is running |
| Port 5000 in use | Change port in `app.py` or kill process |
| Database reset | Delete `hostelhub.db` and run `init_db.py` |

## Database Setup 🗄️

**SQLite (Default - No setup needed)**
```
hostelhub.db will auto-create
```

**MySQL (Production)**
```bash
# Update .env with MySQL credentials
python init_db.py  # Creates database & tables
```

## Security Notes 🔒

⚠️ **Production:**
- Change default admin password immediately
- Generate strong `SECRET_KEY`
- Use MySQL instead of SQLite
- Disable debug mode
- Use HTTPS

## License 📄

MIT License

## Support 📧

For issues or questions, create a GitHub issue.

---

Made with ❤️ for hostel management
