from app import app
from routes import register_routes

# Register all routes
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)