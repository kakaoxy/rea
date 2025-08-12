# Technology Stack

## Core Framework
- **Streamlit**: Web application framework for the dashboard interface
- **Python 3.12**: Primary programming language

## Key Dependencies
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization and charting
- **numpy**: Numerical computing support

## Build System
- **uv**: Modern Python package manager and dependency resolver
- **pyproject.toml**: Project configuration and dependency management

## Common Commands

### Development
```bash
# Install dependencies
uv sync

# Run the application
uv run streamlit run main.py

# Add new dependencies
uv add package-name
```

### Data Processing
- CSV files are processed with pandas for data cleaning and transformation
- Chinese column names are standardized through mapping dictionaries
- Numeric columns are converted with error handling for data quality

## Code Patterns
- Streamlit components organized in logical sections with clear separators
- Helper functions for data analysis (calculate_price_per_sqm_stats, analyze_market_segments)
- Error handling with try-catch blocks for data processing
- Responsive layout using Streamlit columns and containers