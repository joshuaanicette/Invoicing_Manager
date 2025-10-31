# Invoice Management System

A modern, full-featured invoice management system built with Flask and PostgreSQL. Create, edit, delete, and generate professional PDF invoices with ease.

## Features

- **Complete Invoice Management**: Create, view, edit, and delete invoices
- **Multi-Customer Support**: Add multiple customers and items per invoice
- **Professional PDF Generation**: Generate beautiful PDF invoices with detailed formatting
- **Categorized View**: View invoices by year, month, or day
- **Real-time Feedback**: Toast notifications for all operations
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **PostgreSQL Database**: Production-ready relational database
- **Vercel-Ready**: Optimized for serverless deployment

## Tech Stack

- **Backend**: Python 3.x with Flask
- **Database**: PostgreSQL (Vercel Postgres recommended)
- **PDF Generation**: fpdf2 (pure Python, serverless-ready)
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Deployment**: Vercel (serverless functions)

## Quick Start

### Prerequisites

- Python 3.x
- PostgreSQL database
- pip (Python package manager)

### Local Development

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd Invoicing_System_2
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export DATABASE_URL="postgresql://username:password@host:port/database"
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser to `http://localhost:5000`

## Deployment

**🚀 Easiest Way: Use Vercel Postgres (Recommended)**

See [VERCEL_POSTGRES_SETUP.md](VERCEL_POSTGRES_SETUP.md) for the **2-minute setup guide**.

Just 3 steps:
1. Create Vercel Postgres database in your dashboard
2. Connect it to your project
3. Redeploy

No configuration needed - it works automatically! ✨

---

For other deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   vercel
   ```

3. Add your DATABASE_URL:
   ```bash
   vercel env add DATABASE_URL
   ```

4. Deploy to production:
   ```bash
   vercel --prod
   ```

## Project Structure

```
Invoicing_System_2/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel deployment configuration
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   └── script.js          # Frontend JavaScript
├── DEPLOYMENT.md          # Deployment guide
└── README.md              # This file
```

## Usage

### Creating an Invoice

1. Fill in your company information
2. Click "Add Customer" to add customer details
3. Click "Add Item" to add line items for each customer
4. Enter quantities, descriptions, and prices
5. Click "Create Invoice"
6. A PDF will automatically open in a new tab

### Editing an Invoice

1. Click "Edit" on any invoice in the table, or
2. Enter the invoice number and click "Load Invoice"
3. Make your changes
4. Click "Modify Invoice"

### Deleting an Invoice

1. Enter the invoice number in the Delete section
2. Click "Delete Invoice"
3. Confirm the deletion

### Viewing Invoices

- Choose categorization: Year, Month, or Day
- Click "View Invoices" to refresh the list
- Click "PDF" to view the invoice PDF
- Click "Edit" to load the invoice for editing

## API Endpoints

### Invoices

- `GET /api/invoices` - List all invoices
- `POST /api/invoices` - Create a new invoice
- `PUT /api/invoices/:number` - Update an invoice
- `DELETE /api/invoices/:number` - Delete an invoice
- `GET /api/invoices/categorize?period={year|month|day}` - Get categorized invoices
- `GET /api/invoices/:number/pdf` - Generate PDF for an invoice
- `POST /api/invoices/reset` - Check current invoice counter

### Health Check

- `GET /health` - Application health status

## Database Schema

### invoices
- `id` (SERIAL PRIMARY KEY)
- `invoice_number` (INTEGER UNIQUE)
- `creation_date` (TEXT)
- `company_name` (TEXT)
- `company_address` (TEXT)
- `company_email` (TEXT)
- `total_amount` (REAL)

### customers
- `id` (SERIAL PRIMARY KEY)
- `invoice_id` (INTEGER FK)
- `name` (TEXT)
- `address` (TEXT)
- `email` (TEXT)

### items
- `id` (SERIAL PRIMARY KEY)
- `customer_id` (INTEGER FK)
- `description` (TEXT)
- `quantity` (INTEGER)
- `unit_price` (REAL)

## Features in Detail

### Toast Notifications
- Success notifications (green) for successful operations
- Error notifications (red) for failures
- Info notifications (blue) for general information
- Auto-dismiss after 5 seconds

### Loading States
- All buttons show loading spinners during operations
- Buttons are disabled during processing
- Clear visual feedback for all actions

### Form Validation
- Required fields are validated before submission
- Date picker for invoice dates
- Email validation for email fields
- Number validation for quantities and prices

### PDF Features
- Professional header with invoice number
- Company information section
- Customer billing information
- Itemized table with quantities and prices
- Subtotals per customer
- Grand total with highlighted section
- Responsive layout that handles page breaks

## Environment Variables

- `DATABASE_URL` (required): PostgreSQL connection string
- `PORT` (optional): Server port (default: 5000)

## Development

### Running Tests

```bash
# Add your test commands here
python -m pytest
```

### Code Style

The project follows PEP 8 style guidelines for Python code.

## Troubleshooting

### Database Connection Issues

- Verify your `DATABASE_URL` is correct
- Check if PostgreSQL allows remote connections
- Ensure the database exists

### PDF Generation Issues

- Check that ReportLab is installed correctly
- Verify you have write permissions
- Check available memory (PDFs are generated in memory)

### Deployment Issues

- Check Vercel build logs
- Verify environment variables are set
- Ensure PostgreSQL accepts connections from Vercel

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions:
- Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide
- Review the troubleshooting section above
- Open an issue on GitHub

## Acknowledgments

- Built with Flask
- Styled with Tailwind CSS
- PDFs powered by ReportLab
- Deployed on Vercel
