# Stocker - Professional Stock Trading Platform

A high-end, dark-themed stock trading web application designed for serious retail investors and professional-minded traders.

## Features

- **Minimalist Dark Theme**: Professional, institutional-grade dark UI with muted color palette
- **Real-time Portfolio Tracking**: Monitor holdings, performance metrics, and market data
- **Trade Execution**: Buy and sell stocks with multiple order types (Market, Limit, Stop, Stop-Limit)
- **Portfolio Analytics**: Comprehensive performance metrics, sector allocation, and returns analysis
- **Transaction History**: Complete audit trail of all trading activity
- **Admin Panel**: System oversight and user management tools
- **Responsive Design**: Works seamlessly across desktop and mobile devices

## Design Philosophy

- **Data-first**: Clean, readable interface focused on information clarity
- **Institutional Feel**: Confident, precise, and professional aesthetic
- **No Clutter**: Minimal design without flashy effects or unnecessary animations
- **Long-session Friendly**: Carefully chosen colors and contrast for extended use

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Jinja2 Templates, Vanilla CSS/JavaScript
- **Charts**: Chart.js for data visualization
- **Typography**: Inter font family for professional readability

## Installation

1. Clone the repository:
```bash
cd "Capstone Project/Stocker-V2"
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Pages

### Public Pages
- **Landing Page** (`/`) - Hero section with feature highlights
- **Login** (`/login`) - Clean authentication interface
- **Sign Up** (`/signup`) - Account registration

### Authenticated Pages
- **Dashboard** (`/dashboard`) - Portfolio overview with charts and holdings
- **Buy/Sell** (`/buy-sell`) - Stock lookup and trade execution
- **Portfolio** (`/portfolio`) - Detailed holdings and performance metrics
- **Transactions** (`/transactions`) - Complete transaction history
- **Settings** (`/settings`) - Account and preference management
- **Admin** (`/admin`) - System administration and user management

## Color Palette

```css
Primary Background: #0f0f11
Secondary Surface: #18181b
Tertiary Surface: #1e1e22
Elevated Surface: #24242a

Text Primary: #e4e4e7
Text Secondary: #a1a1aa
Text Tertiary: #71717a

Gain/Buy: #22c55e (muted green)
Loss/Sell: #ef4444 (muted red)
Focus/Links: #3b82f6 (subtle blue)
```

## Project Structure

```
Stocker-V2/
├── app.py                 # Flask application and routes
├── requirements.txt       # Python dependencies
├── static/
│   └── css/
│       └── style.css     # Custom dark theme styles
└── templates/
    ├── base.html         # Base template for public pages
    ├── dashboard_base.html # Base template for authenticated pages
    ├── index.html        # Landing page
    ├── login.html        # Login page
    ├── signup.html       # Registration page
    ├── dashboard.html    # Main dashboard
    ├── buy_sell.html     # Trade execution page
    ├── portfolio.html    # Portfolio details
    ├── transactions.html # Transaction history
    ├── settings.html     # Account settings
    └── admin.html        # Admin panel
```

## Design Constraints

- **No gradients** - Flat, solid colors only
- **No neon colors** - Muted, professional palette
- **No glowing effects** - Subtle transitions and hover states only
- **No generic SaaS look** - Custom-designed, production-ready interface
- **Minimal animations** - Opacity and background color transitions only

## Development Notes

- All monetary values use monospace font for better readability
- Tables feature subtle hover states without borders
- Charts use muted colors matching the overall theme
- Form inputs have clear focus states
- Modals use semi-transparent backdrops

## License

This is a demonstration project for educational purposes.

## Author

Built as part of a capstone project showcasing professional UI/UX design principles for financial applications.
