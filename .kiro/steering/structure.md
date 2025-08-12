# Project Structure

## Root Directory
```
├── main.py              # Main Streamlit application entry point
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── .python-version     # Python version specification (3.12)
├── README.md           # Project documentation
└── housing/            # Data directory for CSV files
```

## Data Organization
- **housing/**: Contains real estate data organized by location
  - **jinganpengpu/**: Sample data for Jing'an Pengpu area
    - CSV files with date prefixes (YYYYMMDD format)
    - Separate files for active listings (在售房源) and transactions (成交房源)
  - **pudongjinyang/**: Additional location data directory

## File Naming Conventions
- CSV files: `YYYYMMDD_地区名_数据类型.csv`
- Example: `20250718_彭浦_在售房源.csv`

## Code Organization in main.py
1. **Configuration**: Page setup and imports
2. **Helper Functions**: Data processing utilities
3. **Sidebar Controls**: User interface for filtering and file upload
4. **Data Processing**: CSV loading, cleaning, and standardization
5. **Metrics Display**: Key performance indicators
6. **Filtering Logic**: Dynamic data filtering based on user selections
7. **Visualization**: Charts and graphs using Plotly
8. **Analysis Sections**: Market insights and trend analysis

## Data Schema Expectations
- **Chinese Column Headers**: Application handles Chinese property data columns
- **Standardized Mapping**: Column names are mapped to consistent internal format
- **Numeric Data**: Price, area, and date fields with proper type conversion
- **Geographic Data**: District (区域) and commercial area (商圈) information