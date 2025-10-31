// Frontend logic connecting to Flask backend
console.log('script.js is loading...');
let lastInvoiceNumber = 1000;

// ============ Authentication ============
async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            document.getElementById('userName').textContent = `${user.username} ${user.full_name ? '(' + user.full_name + ')' : ''}`;
        } else if (response.status === 401) {
            // Not authenticated, redirect to login
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
        window.location.href = '/login';
    }
}

async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showToast('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 500);
        } else {
            showToast('Failed to logout', 'error');
        }
    } catch (error) {
        console.error('Error logging out:', error);
        showToast('An error occurred', 'error');
    }
}

// Load user info when page loads
document.addEventListener('DOMContentLoaded', loadUserInfo);

// ============ Toast Notifications ============
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-500 hover:text-gray-700">&times;</button>
        </div>
    `;
    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ============ Loading States ============
function setLoading(buttonId, isLoading, originalText) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = originalText + '<span class="spinner"></span>';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || originalText;
    }
}

// ============ Customer Management ============
function addCustomer(customer = { name: '', address: '', email: '', items: [] }) {
    console.log('addCustomer called with:', customer);
    const customerDiv = document.createElement('div');
    customerDiv.className = 'customer mb-4 p-4 border rounded-md bg-gray-50';
    customerDiv.innerHTML = `
        <div class="mb-2">
            <label class="block text-sm font-medium">Customer Name</label>
            <input type="text" class="customer-name mt-1 p-2 w-full border rounded-md" value="${customer.name}" placeholder="Enter customer name" required>
        </div>
        <div class="mb-2">
            <label class="block text-sm font-medium">Customer Address</label>
            <input type="text" class="customer-address mt-1 p-2 w-full border rounded-md" value="${customer.address}" placeholder="Enter customer address">
        </div>
        <div class="mb-2">
            <label class="block text-sm font-medium">Customer Email</label>
            <input type="email" class="customer-email mt-1 p-2 w-full border rounded-md" value="${customer.email}" placeholder="Enter customer email">
        </div>
        <div class="items mb-2">
            <h3 class="text-sm font-medium mb-2">Items</h3>
            <div class="items-container"></div>
        </div>
        <div class="flex gap-2">
            <button type="button" onclick="addItem(this.parentElement.parentElement)" class="bg-blue-300 text-white px-3 py-1 rounded-md hover:bg-blue-400 transition-all">Add Item</button>
            <button type="button" onclick="this.parentElement.parentElement.remove(); showToast('Customer removed', 'info')" class="bg-red-300 text-white px-3 py-1 rounded-md hover:bg-red-400 transition-all">Remove Customer</button>
        </div>
    `;
    document.getElementById('customers').appendChild(customerDiv);

    // Add existing items or add one empty item by default
    if (customer.items && customer.items.length > 0) {
        customer.items.forEach(item => addItem(customerDiv, item));
    } else {
        addItem(customerDiv);
    }
}

function addItem(customerDiv, item = { description: '', quantity: 1, unit_price: 0 }) {
    const itemsContainer = customerDiv.querySelector('.items-container');
    const itemDiv = document.createElement('div');
    itemDiv.className = 'item flex gap-2 mb-2';
    itemDiv.innerHTML = `
        <input type="text" class="item-description p-2 flex-1 border rounded-md" value="${item.description}" placeholder="Description" required>
        <input type="number" class="item-quantity p-2 w-20 border rounded-md" value="${item.quantity}" placeholder="Qty" min="1" required>
        <input type="number" class="item-unit-price p-2 w-24 border rounded-md" value="${item.unit_price}" placeholder="Price" step="0.01" min="0" required>
        <button type="button" onclick="this.parentElement.remove()" class="bg-red-300 text-white px-3 py-1 rounded-md hover:bg-red-400 transition-all">Remove</button>
    `;
    itemsContainer.appendChild(itemDiv);
}

// ============ Form Data Collection ============
function collectInvoiceData() {
    const invoiceNumber = document.getElementById('invoiceNumber').value;
    const company = {
        name: document.getElementById('companyName').value.trim(),
        address: document.getElementById('companyAddress').value.trim(),
        email: document.getElementById('companyEmail').value.trim()
    };
    const invoiceDate = document.getElementById('invoiceDate').value;

    if (!invoiceDate) {
        showToast('Please enter an invoice date', 'error');
        return null;
    }

    if (!company.name) {
        showToast('Please enter company name', 'error');
        return null;
    }

    const customers = [];
    document.querySelectorAll('.customer').forEach(customerDiv => {
        const items = [];
        customerDiv.querySelectorAll('.item').forEach(itemDiv => {
            const description = itemDiv.querySelector('.item-description').value.trim();
            const quantity = parseInt(itemDiv.querySelector('.item-quantity').value) || 1;
            const unit_price = parseFloat(itemDiv.querySelector('.item-unit-price').value) || 0;

            if (description) {
                items.push({
                    description: description,
                    quantity: quantity,
                    unit_price: unit_price
                });
            }
        });

        if (items.length > 0) {
            const customerName = customerDiv.querySelector('.customer-name').value.trim();
            if (!customerName) {
                showToast('Please enter customer name', 'error');
                return null;
            }

            customers.push({
                name: customerName,
                address: customerDiv.querySelector('.customer-address').value.trim(),
                email: customerDiv.querySelector('.customer-email').value.trim(),
                items: items
            });
        }
    });

    if (customers.length === 0) {
        showToast('Please add at least one customer with items', 'error');
        return null;
    }

    const total_amount = customers.reduce((sum, c) =>
        sum + c.items.reduce((s, i) => s + (i.quantity * i.unit_price), 0), 0
    );

    return {
        invoice_number: invoiceNumber ? parseInt(invoiceNumber) : null,
        company_name: company.name,
        company_address: company.address,
        company_email: company.email,
        creation_date: invoiceDate,
        customers: customers,
        total_amount: total_amount
    };
}

// ============ Invoice Operations ============
async function createInvoice() {
    const data = collectInvoiceData();
    if (!data) return;

    setLoading('createBtn', true, 'Creating');

    try {
        const res = await fetch('/api/invoices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const json = await res.json();

        if (res.ok) {
            showToast(`Invoice #${json.invoice_number} created successfully!`, 'success');
            clearForm();
            viewInvoices();

            // Open PDF in new tab
            setTimeout(() => {
                window.open(`/api/invoices/${json.invoice_number}/pdf`, '_blank');
            }, 500);
        } else {
            showToast(`Failed to create invoice: ${json.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating invoice:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        setLoading('createBtn', false, 'Create Invoice');
    }
}

async function modifyInvoice() {
    const invoiceNumberInput = document.getElementById('invoiceNumber').value;
    if (!invoiceNumberInput) {
        showToast('Please enter an invoice number to modify', 'error');
        return;
    }

    const invoiceNumber = parseInt(invoiceNumberInput);
    const data = collectInvoiceData();
    if (!data) return;

    setLoading('modifyBtn', true, 'Modifying');

    try {
        const res = await fetch(`/api/invoices/${invoiceNumber}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const json = await res.json();

        if (res.ok) {
            showToast(`Invoice #${invoiceNumber} modified successfully!`, 'success');
            clearForm();
            viewInvoices();

            // Open updated PDF
            setTimeout(() => {
                window.open(`/api/invoices/${invoiceNumber}/pdf`, '_blank');
            }, 500);
        } else {
            showToast(`Failed to modify invoice: ${json.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error modifying invoice:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        setLoading('modifyBtn', false, 'Modify Invoice');
    }
}

async function deleteInvoice() {
    const invoiceNumber = document.getElementById('deleteInvoiceNumber').value;
    if (!invoiceNumber) {
        showToast('Please enter an invoice number', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to delete invoice #${invoiceNumber}?`)) {
        return;
    }

    setLoading('deleteBtn', true, 'Deleting');

    try {
        const res = await fetch(`/api/invoices/${invoiceNumber}`, {
            method: 'DELETE'
        });

        const json = await res.json();

        if (res.ok) {
            showToast(`Invoice #${invoiceNumber} deleted successfully`, 'success');
            document.getElementById('deleteInvoiceNumber').value = '';
            viewInvoices();
        } else {
            showToast(`Failed to delete invoice: ${json.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting invoice:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        setLoading('deleteBtn', false, 'Delete Invoice');
    }
}

async function loadInvoice() {
    const invoiceNumber = prompt('Enter invoice number to load:');
    if (!invoiceNumber) return;

    setLoading('loadBtn', true, 'Loading');

    try {
        const res = await fetch('/api/invoices');
        const all = await res.json();
        const inv = all.find(i => parseInt(i.invoice_number) === parseInt(invoiceNumber));

        if (!inv) {
            showToast('Invoice not found', 'error');
            return;
        }

        fillFormWithInvoice(inv);
        showToast(`Invoice #${invoiceNumber} loaded successfully`, 'success');
    } catch (error) {
        console.error('Error loading invoice:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        setLoading('loadBtn', false, 'Load Invoice');
    }
}

function fillFormWithInvoice(inv) {
    document.getElementById('invoiceNumber').value = inv.invoice_number;
    document.getElementById('companyName').value = inv.company_name || '';
    document.getElementById('companyAddress').value = inv.company_address || '';
    document.getElementById('companyEmail').value = inv.company_email || '';
    document.getElementById('invoiceDate').value = inv.creation_date || '';

    // Clear existing customers
    document.getElementById('customers').innerHTML = '';

    // Add customers from invoice
    (inv.customers || []).forEach(c => addCustomer(c));

    // Scroll to top of form
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function clearForm() {
    document.getElementById('invoiceForm').reset();
    document.getElementById('customers').innerHTML = '';

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('invoiceDate').value = today;
}

// ============ View Invoices ============
async function viewInvoices() {
    const period = document.getElementById('viewPeriod').value;
    const loadingIndicator = document.getElementById('loadingIndicator');
    const tbody = document.getElementById('invoicesTableBody');

    loadingIndicator.classList.remove('hidden');
    tbody.innerHTML = '';

    try {
        const res = await fetch(`/api/invoices/categorize?period=${period}`);
        const categorized = await res.json();

        const entries = Object.entries(categorized);

        if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-gray-500">No invoices found</td></tr>';
            return;
        }

        for (const [periodKey, periodInvoices] of entries) {
            periodInvoices.forEach(invoice => {
                const row = document.createElement('tr');
                row.className = 'hover:bg-gray-50 transition-all';

                const customersText = (invoice.customers || [])
                    .map(c => `${c.name} (${c.items ? c.items.length : 0} items)`)
                    .join(', ') || 'No customers';

                row.innerHTML = `
                    <td class="p-2 border">${periodKey}</td>
                    <td class="p-2 border font-semibold">${invoice.invoice_number}</td>
                    <td class="p-2 border">${invoice.creation_date}</td>
                    <td class="p-2 border text-sm">${customersText}</td>
                    <td class="p-2 border text-right font-semibold">$${(invoice.total_amount || 0).toFixed(2)}</td>
                    <td class="p-2 border text-center">
                        <div class="flex gap-1 justify-center">
                            <button type="button" onclick="loadInvoiceForEdit(${invoice.invoice_number})"
                                class="bg-yellow-500 text-white px-2 py-1 rounded-md hover:bg-yellow-600 transition-all text-sm">
                                Edit
                            </button>
                            <button type="button" onclick="viewInvoicePDF(${invoice.invoice_number})"
                                class="bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600 transition-all text-sm">
                                PDF
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error viewing invoices:', error);
        showToast('Failed to load invoices', 'error');
        tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-red-500">Failed to load invoices</td></tr>';
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

async function loadInvoiceForEdit(invoiceNumber) {
    try {
        const res = await fetch('/api/invoices');
        const all = await res.json();
        const inv = all.find(i => parseInt(i.invoice_number) === parseInt(invoiceNumber));

        if (!inv) {
            showToast('Invoice not found', 'error');
            return;
        }

        fillFormWithInvoice(inv);
        showToast(`Invoice #${invoiceNumber} loaded for editing`, 'info');
    } catch (error) {
        console.error('Error loading invoice:', error);
        showToast('Failed to load invoice', 'error');
    }
}

function viewInvoicePDF(invoiceNumber) {
    window.open(`/api/invoices/${invoiceNumber}/pdf`, '_blank');
}

// ============ Reset Invoice Number ============
async function resetInvoiceNumber() {
    setLoading('resetBtn', true, 'Checking');

    try {
        const res = await fetch('/api/invoices/reset', { method: 'POST' });
        const json = await res.json();

        if (res.ok) {
            lastInvoiceNumber = json.lastInvoiceNumber || 1000;
            showToast(`Current invoice counter: ${lastInvoiceNumber}. Next invoice will be #${lastInvoiceNumber + 1}`, 'info');
        } else {
            showToast('Failed to check invoice counter', 'error');
        }
    } catch (error) {
        console.error('Error checking invoice counter:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        setLoading('resetBtn', false, 'Check Counter');
    }
}

// ============ Initialization ============
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing...');

    try {
        // Set today's date as default
        const today = new Date().toISOString().split('T')[0];
        const dateInput = document.getElementById('invoiceDate');
        if (dateInput) {
            dateInput.value = today;
        }

        // Show welcome message
        showToast('Invoice Manager loaded successfully', 'success');

        // Load invoices on page load (don't let this block if it fails)
        setTimeout(() => {
            viewInvoices().catch(err => {
                console.error('Failed to load invoices on startup:', err);
            });
        }, 100);
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Error initializing page. Please refresh and check console for details.');
    }
});
