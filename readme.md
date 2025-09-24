# Financial Reports Field Extractor

An automated pipeline for extracting structured financial data from PDF quarterly reports and converting them into standardized Excel format. This tool is designed for Obsidian Cap to process multi-billion dollar AUM fund reports.

## 🚀 Overview

This system processes PDF financial reports through a 3-step pipeline:
1. **PDF → Markdown**: Converts PDFs to structured markdown using Docling
2. **AI Extraction**: Uses GPT-4 to extract financial data into structured JSON
3. **Excel Export**: Combines all data into a color-coded Excel spreadsheet

## 📋 What It Extracts

The tool extracts **80+ financial metrics** per asset including:

### Fund-Level Data
- NAV dates, valuation dates, reporting periods
- Fund names, ISINs, strategies (VC, Growth, Buyout, etc.)
- Investment performance metrics (TVPI, IRR)
- Geographic distribution and currency information
- Hedging strategies and fund commitments

### Asset-Level Financial Metrics
- **Valuation Data**: Enterprise Value, EBITDA, Revenue, Margins
- **Financial Ratios**: EV/EBITDA, EV/Revenue, Debt/Equity ratios
- **Performance Metrics**: Free Cash Flow, Net Results, Gross Profit
- **Risk Metrics**: Credit ratings, spreads, discount rates, betas
- **Real Estate**: Area, segment classification, LTV ratios
- **Investment Details**: Entry/exit dates, ownership percentages

## 🛠️ Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd mcp_project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure OpenAI API**
   Create `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 📖 Usage

### Basic Command
```bash
python main.py <reports_folder> <output_folder>
```

### Example
```bash
python main.py reports out
```

This will:
- Process all PDFs in `reports/` folder
- Extract financial data using AI
- Generate `portfolio_output.xlsx` in `out/` folder

## 🔄 Pipeline Process

### Step 1: PDF Processing (`file_data_extraction.py`)
- Uses **Docling** to convert PDFs to markdown
- Preserves table structures and formulas
- Handles complex financial document layouts
- Outputs: `*.md` files in output folder

### Step 2: AI Field Extraction (`agent_field_matching.py`)
- Uses **GPT-4** with structured output
- Maps financial data to standardized Pydantic models
- Validates data types (decimals, dates, enums)
- Handles K/M/B notation (1.2M → 1,200,000)
- Outputs: `*.json` files with structured data

### Step 3: Excel Export (`excel_exporting.py`)
- Combines all JSON data into single Excel file
- Applies **color-coded headers** by data category
- Maintains consistent column ordering
- Outputs: `portfolio_output.xlsx`

## 📊 Output Format

The Excel file includes **color-coded columns**:

- 🟤 **Dates** (beige): NAV_Date, Valuation_Date
- ⚫ **Fund Info** (gray): Fund identification and ISINs
- 🔵 **Fund Details** (light blue): Strategies, currencies, hedging
- 🟡 **Asset Info** (light yellow): Company names, geographies
- 🟣 **Investment Metrics** (pink): Performance, valuations, TVPI/IRR
- 🟢 **Financial Data** (light green): Revenue, EBITDA, ratios
- 🟠 **Risk Metrics** (orange): Credit ratings, spreads, sensitivities
- 🟢 **Real Estate** (green): Area, segments, LTV

## 📁 Project Structure

```
mcp_project/
├── main.py                    # Entry point - runs 3-step pipeline
├── file_data_extraction.py   # PDF → Markdown conversion
├── agent_field_matching.py   # AI-powered data extraction
├── excel_exporting.py        # Excel export with formatting
├── models.py                 # Pydantic data models (80+ fields)
├── requirements.txt          # Dependencies (pip freeze output)
├── reports/                  # Input PDF files
│   ├── *.pdf                # Quarterly fund reports
├── out/                     # Output directory
│   ├── *.md                 # Converted markdown files
│   ├── *.json               # Extracted structured data
│   └── portfolio_output.xlsx # Final Excel output
└── expected_output/         # Sample output files
```

## 🔧 Configuration

### AI Model Settings
In `agent_field_matching.py`:
```python
llm_structured = ChatOpenAI(
    model="gpt-4.1",  # Change model here
    temperature=1
)
```

### Data Validation
The `models.py` file defines comprehensive validation:
- **Decimal parsing**: Handles K/M/B notation, percentages, basis points
- **Date parsing**: Supports multiple formats (ISO, quarters, "as of" dates)
- **Enum validation**: Standardized values for strategies, geographies, sectors
- **Currency handling**: Automatic symbol detection and conversion

## 📈 Performance & Accuracy

- **Processing Speed**: ~2-5 minutes per PDF (depending on size and complexity)
- **Accuracy**: High accuracy with GPT-4 structured output and validation
- **Scalability**: Handles batch processing of multiple reports
- **Error Handling**: Continues processing if individual files fail

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Key**
   - Ensure `.env` file exists with `OPENAI_API_KEY=your_key`
   - Check API key has sufficient credits

2. **PDF Processing Errors**
   - Some complex PDFs may require manual review
   - Check if PDFs are password-protected or corrupted

3. **Memory Issues**
   - Large PDFs may require significant RAM
   - Consider processing smaller batches

4. **Rate Limits**
   - OpenAI API has usage limits
   - Add delays between requests if needed

### Error Handling
The pipeline includes comprehensive error handling:
- Individual file failures don't stop the entire process
- Detailed error logging for debugging
- Graceful degradation for missing fields

## 🔒 Security & Privacy

- API keys stored in `.env` file (not committed to git)
- No sensitive data logged to console
- All processing happens locally
- PDF files remain on your system

## 📝 Data Model

The system uses Pydantic models for data validation:

- **FundExposure**: Main data structure with 80+ fields
- **AssetSnapshot**: Per-asset financial metrics
- **Enums**: Standardized values for strategies, geographies, sectors
- **Validators**: Automatic type conversion and validation

## 🎯 Use Cases

This tool is specifically designed for:
- **Fund of Funds reporting**: Processing quarterly investor reports
- **Portfolio analysis**: Standardizing data across multiple funds
- **Compliance reporting**: Extracting required regulatory data
- **Performance tracking**: Monitoring fund and asset performance

## 📊 Sample Data

The `reports/` folder contains sample quarterly reports from various fund managers including:
- Crescent Credit Solutions
- HGGC Fund IV
- Potentia Fund II
- Hg Genesis 10 LP

## 🤝 Contributing

For internal development:
1. Follow existing code structure and patterns
2. Update Pydantic models for new field requirements
3. Test with various PDF formats and layouts
4. Maintain backward compatibility

## 📄 License

This project is proprietary software for Obsidian Cap.

---

**Note**: This tool is specifically designed for Obsidian Cap's fund reporting requirements and processes financial data according to their standardized field mappings.