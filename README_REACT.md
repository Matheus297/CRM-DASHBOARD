# React + Vite Transformation

I have transformed your project into a modern React + Vite application with a Flask backend API.

## Project Structure

- **frontend/**: Contains the React application (Vite).
  - `src/pages/`: React components for each page (Dashboard, Login, etc.).
  - `src/context/`: AuthContext for managing login state.
  - `src/Layout.jsx`: Main layout component matching the original `base.html`.
- **backend** (Root): The Flask application is now an API.
  - `routes.py`: Updated to return JSON responses instead of rendering templates.
  - `app.py`: Configured with CORS to allow requests from the frontend.

## How to Run

You need to run both the backend and the frontend.

### 1. Start the Backend

Open a terminal in the root directory (`d:\CrmDashboard`) and run:

```bash
python main.py
```

The backend will start on `http://127.0.0.1:5000`.

### 2. Start the Frontend

Open a **new terminal**, navigate to the `frontend` directory, and run the development server:

```bash
cd frontend
npm run dev
```

The frontend will start (usually on `http://localhost:5173`). Open this URL in your browser to use the application.

## Notes

- **Layout**: The layout has been recreated using React Bootstrap to match the original design.
- **Authentication**: Login/Logout functionality is fully implemented using the existing database.
- **Dashboard**: The dashboard displays real data from the backend.
- **Placeholders**: Some pages (Leads, Settings, etc.) are currently placeholders. You can implement them following the pattern used in `Dashboard.jsx`.
