import pandas as pd

def export_year_sheet(writer, sheet_name, tables):
    current_row = 0
    for table in tables:
        title = table["title"]
        dataframe = table["data"]

        # Write title
        pd.DataFrame([[title]]).to_excel(
            writer,
            sheet_name=sheet_name,
            startrow=current_row,
            startcol=0,
            header=False,
            index=False
        )

        current_row += 1

        # Write table
        dataframe.to_excel(
            writer,
            sheet_name=sheet_name,
            startrow=current_row,
            startcol=0,
            index=False
        )

        # Move cursor down
        current_row += len(dataframe) + 5