# Terminal Dashboard

[![CI/CD Pipeline](https://github.com/dfxnoodle/terminal-dashboard/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/dfxnoodle/terminal-dashboard/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)

A real-time dashboard for monitoring terminal operations with data from Odoo v17.

## Features

- **Forwarding Orders Tracking**: Monitor train departures with weekly comparisons
- **Truck Orders Management**: Track first-mile (NDP) and last-mile (ICAD/DIC) truck operations
- **Stockpile Utilization**: Visual representation of inventory storage across terminals
- **Real-time Updates**: Auto-refresh capabilities with health monitoring
- **Responsive Design**: Modern UI built with Vue 3 and Tailwind CSS

## Architecture

### Backend
- **FastAPI**: High-performance Python web framework
- **Odoo XML-RPC**: Integration with Odoo v17 via External API
- **Python 3.8+**: Modern Python with type hints and async support

### Frontend
- **Vue 3**: Progressive JavaScript framework with Composition API
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
   # Edit .env with your Odoo credentials
   ```

3. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Start the application:**
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
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_API_KEY=your_api_key
```

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
