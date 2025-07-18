import argparse
import pdfplumber
import csv
import re
from datetime import datetime

def extract_transactions_from_bilt_statement(file_path, output_path=None):
    """Extract transactions from Wells Fargo Bilt PDF statement and save to CSV"""
    
    transactions = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if not page_text:
                continue
                
            lines = page_text.split('\n')
            
            # Look for transaction header to identify transaction section
            transaction_section = False
            header_found = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Identify transaction header
                if "Trans Date" in line and "Post Date" in line and "Amount" in line:
                    transaction_section = True
                    header_found = True
                    print(f"Found transaction header on page {page_num}, line {i+1}")
                    continue
                
                # Stop at section breaks
                if transaction_section and any(section in line for section in [
                    "Cash Advances", "Fees Charged", "Interest Charged", 
                    "2024 Totals", "BiltProtect Summary", "Continued on next page"
                ]):
                    if "Continued on next page" not in line:
                        transaction_section = False
                    continue
                
                # Extract transaction data
                if transaction_section and line:
                    # Look for lines that start with MM/DD pattern
                    if re.match(r'^\d{2}/\d{2}', line):
                        transaction = parse_transaction_line(line, lines, i)
                        if transaction:
                            transactions.append(transaction)
                            print(f"Extracted: {transaction}")
    
    # Save to CSV
    if not output_path:
        output_path = file_path.replace('.pdf', '_transactions.csv')
    
    save_transactions_to_csv(transactions, output_path)
    print(f"\nExtracted {len(transactions)} transactions to {output_path}")
    
    return transactions

def parse_transaction_line(line, all_lines, line_index):
    """Parse a single transaction line, handling multi-line transactions"""
    
    # Pattern to match the transaction format
    # 07/26 07/26 230001700 5270487K10PYZ1F85 CHICK-FIL-A WASHINGTON DC $13.74
    pattern = r'^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(\w+)\s+(\w+)\s+(.+?)\s+(\$[\d,]+\.?\d*-?)$'
    
    match = re.match(pattern, line)
    if not match:
        return None
    
    trans_date = match.group(1)
    post_date = match.group(2)
    ref_number = match.group(3)
    transaction_id = match.group(4)
    description_and_amount = match.group(5) + " " + match.group(6)
    
    # Extract amount (last dollar amount in the line)
    amount_matches = re.findall(r'\$[\d,]+\.?\d*-?', description_and_amount)
    if not amount_matches:
        return None
    
    amount = amount_matches[-1]
    
    # Description is everything except the last amount
    description = description_and_amount.replace(amount, '').strip()
    
    # Handle multi-line transactions (like Amtrak)
    # Check if next lines don't start with date pattern and might be continuation
    next_line_index = line_index + 1
    while (next_line_index < len(all_lines) and 
           all_lines[next_line_index].strip() and
           not re.match(r'^\d{2}/\d{2}', all_lines[next_line_index]) and
           not any(section in all_lines[next_line_index] for section in [
               "Cash Advances", "Fees Charged", "Interest Charged", 
               "2024 Totals", "BiltProtect Summary", "Continued on next page"
           ])):
        continuation = all_lines[next_line_index].strip()
        # Only add if it doesn't look like a new transaction or section
        if continuation and not re.match(r'^\d{2}/\d{2}', continuation):
            description += " " + continuation
        next_line_index += 1
    
    # Clean up amount - remove $ and handle negatives
    amount_clean = amount.replace('$', '').replace(',', '')
    if amount_clean.endswith('-'):
        amount_clean = '-' + amount_clean[:-1]
    
    try:
        amount_float = float(amount_clean)
    except ValueError:
        print(f"Warning: Could not parse amount '{amount}' in line: {line}")
        return None
    
    # Add year to dates (assume current year or statement year)
    # You might want to extract the year from the statement date
    current_year = datetime.now().year
    trans_date_full = f"{trans_date}/{current_year}"
    post_date_full = f"{post_date}/{current_year}"
    
    return {
        'trans_date': trans_date_full,
        'post_date': post_date_full,
        'reference_number': ref_number,
        'transaction_id': transaction_id,
        'description': description.strip(),
        'amount': amount_float
    }

def save_transactions_to_csv(transactions, output_path):
    """Save transactions to CSV file"""
    
    if not transactions:
        print("No transactions to save")
        return
    
    fieldnames = ['trans_date', 'post_date', 'reference_number', 'transaction_id', 'description', 'amount']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

def analyze_extracted_transactions(transactions):
    """Analyze the extracted transactions for validation"""
    
    print("\n" + "="*60)
    print("TRANSACTION ANALYSIS")
    print("="*60)
    
    if not transactions:
        print("No transactions found")
        return
    
    print(f"Total transactions: {len(transactions)}")
    
    # Calculate totals
    total_amount = sum(t['amount'] for t in transactions)
    positive_total = sum(t['amount'] for t in transactions if t['amount'] > 0)
    negative_total = sum(t['amount'] for t in transactions if t['amount'] < 0)
    
    print(f"Total amount: ${total_amount:.2f}")
    print(f"Total debits: ${positive_total:.2f}")
    print(f"Total credits: ${negative_total:.2f}")
    
    # Date range
    dates = [t['trans_date'] for t in transactions]
    print(f"Date range: {min(dates)} to {max(dates)}")
    
    # Sample transactions
    print("\nSample transactions:")
    for i, transaction in enumerate(transactions[:5]):
        print(f"  {i+1}. {transaction['trans_date']} - {transaction['description'][:50]}... - ${transaction['amount']:.2f}")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Extract transactions from Wells Fargo Bilt PDF statement")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output", help="Output CSV file path")
    parser.add_argument("--analyze", action="store_true", help="Show transaction analysis")
    
    args = parser.parse_args()
    
    # Extract transactions
    transactions = extract_transactions_from_bilt_statement(args.pdf_path, args.output)
    
    # Analyze if requested
    if args.analyze:
        analyze_extracted_transactions(transactions)

if __name__ == "__main__":
    main()