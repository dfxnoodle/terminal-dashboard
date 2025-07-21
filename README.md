# Terminal Dashboard

[![CI/CD Pipeline](https://github.com/dfxnoodle/terminal-dashboard/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/dfxnoodle/terminal-dashboard/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)

A real-time dashboard for monitoring terminal operations with data from Odoo v17 and comprehensive role-based authentication.

## Features

- **Role-Based Authentication**: Multi-user system with Admin, Operator, Executive, and Visitor roles
- **User Management**: Complete CRUD operations for user accounts with role-based permissions
- **Secure Authentication**: JWT tokens, bcrypt password hashing, and SQLite database storage
- **Forwarding Orders Tracking**: Monitor train departures with weekly comparisons
- **Truck Orders Management**: Track first-mile (NDP) and last-mile (ICAD/DIC) truck operations
- **Stockpile Utilization**: Visual representation of inventory storage across terminals
- **Real-time Updates**: Auto-refresh capabilities with health monitoring
- **Responsive Design**: Modern UI built with Vue 3 and Tailwind CSS
- **System Admin Protection**: Environment-based admin account with credential protection

## Architecture

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLite + SQLAlchemy**: Async database with user management
- **JWT Authentication**: Secure token-based authentication system
- **Bcrypt**: Password hashing for security
- **Odoo XML-RPC**: Integration with Odoo v17 via External API
- **Python 3.8+**: Modern Python with type hints and async support

### Frontend
- **Vue 3**: Progressive JavaScript framework with Composition API
- **Pinia**: Modern state management for authentication
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Access to Odoo v17 instance with External API enabled

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dfxnoodle/terminal-dashboard.git
   cd terminal-dashboard
   ```

2. **Setup environment:**
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your Odoo credentials AND admin user details
   ```

3. **Configure Authentication:**
   ```env
   # Add to your .env file
   ADMIN_USERNAME=your_admin_username
   ADMIN_PASSWORD=your_secure_password
   SECRET_KEY=your_jwt_secret_key_here
   ```

4. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

5. **Start the application:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   **For network access (expose to other devices):**
   ```bash
   ./start.sh --network
   ```

### Manual Setup

#### Backend Setup
```bash
cd backend

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start the server
uv run python main.py
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Getting Started

### First Time Setup

1. Complete the installation steps above
2. The system will automatically create a System Administrator account using credentials from your `.env` file
3. Access the application at `http://localhost:3003`
4. Login with your admin credentials to access the user management interface
5. Create additional users with appropriate roles (Operator, Executive, Visitor)

### User Roles & Permissions

- **System Administrator**: Full access to all features and user management (protected from editing)
- **Admin**: Can manage users and access all dashboard features
- **Operator**: Can view and interact with operational data
- **Executive**: Can view executive-level reports and summaries
- **Visitor**: Read-only access to basic dashboard information

### User Management

Navigate to the User Management section (admin access required) to:
- Create new users with specific roles
- Edit existing user information
- Delete users (except System Administrator)
- View user creation history and roles

## Running the Application

### Local Development (Default)
```bash
./start.sh
```
- Frontend: http://localhost:3003
- Backend: http://localhost:8003

### Network Exposed (Accessible from other devices)
```bash
./start.sh --network
```
- Frontend: http://0.0.0.0:3003 (accessible from network)
- Backend: http://0.0.0.0:8003 (accessible from network)

**Note:** When using `--network` flag, ensure your firewall settings allow access to ports 3003 and 8003.

### Command Line Options
- `--network` or `--expose`: Expose services to network (0.0.0.0)
- `-h` or `--help`: Show help message

## API Endpoints

### Authentication
- `POST /api/auth/login` - User authentication with email/password
- `POST /api/auth/logout` - Logout and token invalidation
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user information

### User Management (Admin/System Admin only)
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `PUT /api/users/{user_id}` - Update user (restrictions apply to System Admin)
- `DELETE /api/users/{user_id}` - Delete user (cannot delete System Admin)

### Dashboard Data
- `GET /api/health` - Health check and connection status
- `GET /api/dashboard/forwarding-orders` - Train departure data
- `GET /api/dashboard/first-mile-truck` - NDP terminal truck orders
- `GET /api/dashboard/last-mile-truck/{terminal}` - ICAD/DIC truck orders
- `GET /api/dashboard/stockpiles` - Stockpile utilization data
- `GET /api/dashboard/all` - All dashboard data in one request

## Dashboard Components

### 1. Forwarding Orders (Train Departures)
- Tracks orders with status "NDP Train Departed" or "Train Arrived at Destination"
- Compares current week vs last week
- Shows daily breakdown
- Week starts Monday 00:00

### 2. First Mile Truck Orders (NDP Terminal)
- Terminal: NDP
- Statuses: "Gate-out Completed", "Train Departed", "Exception"
- Shows today's orders and total weight delivered

### 3. Last Mile Truck Orders (ICAD Terminal)
- Terminal: ICAD
- Statuses: "Gate-out Completed", "Order Completed and Closed"
- Shows today's orders and total weight delivered

### 4. Last Mile Truck Orders (DIC Terminal)
- Terminal: DIC
- Statuses: "Gate-out Completed", "Order Completed and Closed"
- Shows today's orders and total weight delivered

### 5. Stockpile Utilization
- Visual representation of storage capacity vs current stock
- Shows material type and age
- Supports 8-16 stockpiles (ICAD) and 4-8 stockpiles (DIC)

## Data Models

The dashboard integrates with these Odoo models:

- `x_fwo` - Forwarding Orders
- `x_first_mile_freight` - First Mile Truck Orders
- `x_last_mile_freight` - Last Mile Truck Orders
- `x_stockpile` - Stockpiles (Inventory)
- `x_material` - Bulk Materials

## Development

### Project Structure
```
terminal-dashboard/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── odoo_api.py      # Odoo integration
│   └── pyproject.toml   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── services/    # API service
│   │   └── App.vue      # Main app component
│   ├── package.json     # Node.js dependencies
│   └── vite.config.js   # Vite configuration
├── .env                 # Environment variables
└── README.md
```

### Adding New Dashboard Items

1. **Backend**: Add new method to `OdooAPI` class in `odoo_api.py`
2. **API**: Add new endpoint in `main.py`
3. **Frontend**: Add new component in `src/components/`
4. **Integration**: Update dashboard view in `src/views/Dashboard.vue`

### Environment Variables

```env
# Odoo Configuration
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_API_KEY=your_api_key

# Authentication Configuration
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_jwt_secret_key_here
```

### Security Configuration

#### JWT Secret Key
Generate a secure random key for JWT token signing:
```bash
# Generate secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Admin Password
Use a strong password for the System Administrator account. This password is used for initial setup and cannot be changed through the web interface.

## Deployment

### Docker Deployment

1. **Using Docker Compose (Recommended):**
   ```bash
   # Copy environment file
   cp .env.example .env
   # Edit .env with your configuration
   
   # Start the application
   docker-compose up -d
   ```

2. **Using Docker:**
   ```bash
   # Build the image
   docker build -t terminal-dashboard .
   
   # Run the container
   docker run -d -p 8000:8000 --env-file .env terminal-dashboard
   ```

### Manual Production Deployment
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production Frontend
```bash
cd frontend
npm run build
# Serve the dist/ folder with your preferred web server
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify Odoo credentials in `.env`
   - Ensure API key is correct and user has proper permissions

2. **Connection Refused**
   - Check if Odoo instance is accessible
   - Verify network connectivity and firewall settings

3. **Missing Data**
   - Ensure required Odoo models exist
   - Check field names match your Odoo customization

4. **Frontend Not Loading**
   - Verify backend is running on port 8000
   - Check browser console for errors

### Logs

Backend logs are displayed in the terminal where you started the FastAPI server. Frontend logs are available in the browser's developer console.

## Project Status

### ✅ Completed Features

- **Role-Based Authentication System**: Complete multi-user authentication with Admin, Operator, Executive, and Visitor roles
- **User Management Interface**: Full CRUD operations for user accounts with role-based permissions
- **System Admin Protection**: Environment-based admin account with credential protection
- **JWT Security**: Secure token-based authentication with bcrypt password hashing
- **SQLite Integration**: Async database operations with user management and role tracking
- **Full Odoo Integration**: Successfully connected to Odoo v17 using External API
- **Real-time Data Fetching**: Backend fetches actual data from Odoo models:
  - `x_fwo` (Forwarding Orders) - Train departure tracking
  - `x_first_mile_freight` (First Mile Truck Orders) - NDP terminal operations
  - `x_last_mile_freight` (Last Mile Truck Orders) - ICAD/DIC terminal operations
  - `x_stockpile` (Stockpile Utilization) - 18 real stockpiles from ICAD and DIC terminals
- **Modern UI/UX**: Responsive design with Vue 3, Tailwind CSS, and optimized spacing
- **Network Accessibility**: Application can run locally or be exposed to network
- **CORS Resolution**: Proper cross-origin request handling for both local and network modes
- **GitHub Ready**: Complete project setup with CI/CD, Docker, documentation, and licensing
- **Production Ready**: Error handling, health checks, and proper logging

### 📊 Live Data Integration

The dashboard now displays **real-time data from Odoo** including:
- **ICAD Terminal**: 14 active stockpiles with real capacities, quantities, and material types
- **DIC Terminal**: 4 active stockpiles with live inventory data
- **Material Tracking**: Actual limestone types (WBG, SR, ALAA, Ri Si) with aging information
- **Utilization Metrics**: Real-time capacity utilization percentages

### 🚀 Ready for Deployment

The project is fully prepared for:
- Local development and testing
- Network deployment in production environments
- Docker containerization
- GitHub collaboration and version control

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review Odoo External API documentation
- Create an issue in the repository
