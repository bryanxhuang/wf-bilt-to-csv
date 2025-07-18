# Wells Fargo Bilt PDF Bank Statement to CSV Extractor

With the news of Wells Fargo splitting up with Bilt, I built this free, offline tool to convert their PDF Bank Statements to CSV.

Wells Fargo does not allow users to export by `.csv` past 120 days for credit cards. Compared to most large retail banks, this makes even a year's worth of transactions pretty unmanageable to do by hand.

A `.csv` format is useful for taxes, budgeting, and accounting.

## Acknowledgements
- Thanks to [Julian Kingman](https://github.com/JulianKingman/wells-fargo-statement-to-csv) for the original work getting a PDF parser to work.

His original README:
```
Do you have PDF statements, but want to do something useful for them? Never fear, statement extractor is here!
Things you need:
 - Python
 - pdfplumber (installed via pip or something)
 - Run `python convertStatement.py "011516 WellsFargo.pdf"`
You will receive a shiny new CSV file with its beautiful contents.

## Combine CSVs
This will combine multiple statements in a directory (recursively).
Things you need:
 - pandas (pip install pandas)
 - Run `python combineCSVByDate.py my-converted-csv-folder`

Note: csvs get overwritten without warning, so if you modify a csv, don't overwrite it!

This took a lot of trial and error and pain, profit from my suffering!
```