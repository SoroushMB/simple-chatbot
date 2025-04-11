# Gemini Chatbot

A simple, responsive chatbot application built with Flask, SQLite, and the Gemini API. This application features user authentication, chat functionality, and admin controls.

![Gemini Chatbot Screenshot](screenshot.png)

## Features

### User Features
- **Authentication**: Register and login with email/password
- **Chat Interface**: Communicate with Gemini AI
- **Message History**: View and save chat history
- **Profile Management**: Update password and view account details
- **Daily Message Limits**: Configurable limits on message frequency
- **Dark/Light Mode**: Toggle between themes with animated transitions

### Admin Features
- **Dashboard**: View user and message statistics
- **User Management**: View, activate/deactivate, and delete users
- **Message Limits**: Set daily message limits for each user
- **Chat History**: View all users' chat histories

### UI Features
- **Responsive Design**: Mobile-friendly layout using Tailwind CSS
- **Animations**: Smooth transitions and loading effects
- **Random Mind Logo**: Different logo displayed on each chat page load
- **DM Sans Font**: Clean, modern typography
- **Dark Mode Support**: Complete dark theme with smooth transitions

## Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **AI Integration**: Google Generative AI (Gemini API)
- **Authentication**: Werkzeug security for password hashing

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gemini-chatbot.git
   cd gemini-chatbot
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install flask google-generativeai werkzeug python-dotenv
   ```

4. Set up environment variables by creating a `.env` file:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit the .env file with your actual values
   # Replace the placeholder values with your actual API keys and secrets
   ```

5. Initialize the database:
   ```bash
   flask init-db
   ```

6. Run the application:
   ```bash
   flask run
   ```

8. Open your browser and navigate to ```http://127.0.0.1:5000/```

## Default Admin Credentials

- **Email**: admin@example.com
- **Password**: admin

## Project Structure

```
gemini_chatbot/
├── app.py                  # Main Flask application
├── schema.sql              # Database schema
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Example environment variables file
├── static/
│   ├── css/
│   │   └── style.css       # Custom CSS (not used with Tailwind)
│   └── images/
│       ├── mind1.svg       # Random mind logos
│       ├── mind2.svg
│       └── mind3.svg
└── templates/
    ├── admin/
    │   ├── dashboard.html  # Admin dashboard
    │   ├── user_chats.html # User chat history
    │   └── users.html      # User management
    ├── auth/
    │   ├── login.html      # Login page
    │   └── register.html   # Registration page
    ├── base.html           # Base template
    ├── chat.html           # Chat interface
    └── profile.html        # User profile
```

## Notes

1. This implementation uses SQLite for simplicity. For production, consider using a more robust database.
2. The Gemini API key should be kept in the `.env` file and never committed to version control.
3. The application includes basic error handling, but you might want to enhance it for production use.
4. The mind logos are simple SVG files that change randomly on each chat page load.
5. The application enforces daily message limits per user, configurable by the admin.

## License

MIT

## Acknowledgements

- Google for the Gemini API
- Flask team for the excellent web framework
- Tailwind CSS for the utility-first CSS framework
