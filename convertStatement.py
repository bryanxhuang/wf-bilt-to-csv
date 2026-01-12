#!/usr/bin/env python3
import argparse
import pdfplumber
import re
import csv

def extract_transactions(pdf_path, output_csv):
    date_re = re.compile(r'^\d{2}/\d{2}/\d{2}')
    amt_re  = re.compile(r'\$?([\d,]+\.\d{2})$')

    # 1) Read every line from every page
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for L in text.splitlines():
                lines.append(L.strip())

    # 2) Walk through lines, picking out date-started blocks
    transactions = []
    i = 0
    while i < len(lines):
        L = lines[i]
        if date_re.match(L):
            # parse date + amount on this line
            date = L[:8]
            # try to pull amount at end
            m_amt = amt_re.search(L)
            if m_amt:
                amount = m_amt.group(1)
                # description is everything between date and amount
                desc = L[9: m_amt.start()].strip()
            else:
                amount = ""
                desc = L[9:].strip()

            # 3) append any following lines until next date or blank or lone "t"
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if date_re.match(nxt) or nxt == "" or nxt.lower() == "t":
                    break
                desc += " " + nxt
                j += 1

            transactions.append({
                "date": date,
                "description": desc,
                "amount": amount
            })
            i = j
        else:
            i += 1

    # 4) write CSV
    if not transactions:
        print("❌ No transactions found.")
        return

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["date","description","amount"])
        w.writeheader()
        w.writerows(transactions)

    print(f"✅ Extracted {len(transactions)} transactions to {output_csv}")

def main():
    p = argparse.ArgumentParser(
        description="Extract MM/DD/YY transactions from PDF into CSV"
    )
    p.add_argument("pdf_path", help="Path to the statement PDF")
    p.add_argument(
        "-o","--output",
        default=None,
        help="CSV file to write"
    )
    args = p.parse_args()
    # If no -o given, use PDF’s basename + .csv
    out = args.output or args.pdf_path.rsplit(".",1)[0] + ".csv"
    extract_transactions(args.pdf_path, out)

if __name__=="__main__":
    main()