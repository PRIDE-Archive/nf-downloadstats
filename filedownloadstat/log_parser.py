import gzip
import sys
from datetime import datetime


class LogParser:
    """
    Class to parse the log file into parquet format
    """

    def __init__(self, file_path):
        self.file_path = file_path

    def parse_gzipped_tsv(self):
        """
        Read the gzipped TSV file and parse each line
        :return:
        """
        parsed_data = []
        PRIDE_BASE_PATH = '/pride/data/archive'

        try:
            with gzip.open(self.file_path, 'rt') as file:  # 'rt' mode for reading text
                for line in file:
                    line = line.replace('\\t', '\t')  # Replace literal '\t' with actual tab
                    row = line.strip().split('\t')  # Split each line by tab
                    if row[3].startswith(PRIDE_BASE_PATH) and row[6].lower().strip() == 'complete':  # pass only PRIDE data and complete
                        parsed_line = self.parse_row(row)
                        if parsed_line:
                            parsed_data.append(parsed_line)
        except Exception as e:
            raise e.with_traceback(sys.exc_info()[2])
        return parsed_data

    def parse_row(self, row):
        """
        Define a function to parse each row by extracting fields by column index
        :param row:
        :return:
        """
        DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

        try:
            dt = datetime.strptime(row[0], DATETIME_FORMAT)
            year = dt.year
            month = dt.month
            date = dt.date()

            return {
                "date": date,  # Date
                "year": year,
                "month": month,
                "accession": row[3].split('/')[-2],  # Extract the PXD Accession from the path
                "filename": row[3].split('/')[-1],  # Extract the Filename from the path
                "completed": row[6].lower().strip(),  # Completion Status (e.g., Complete or Incomplete)
                "country": row[7],  # Country
                "method": row[11],  # Method (e.g., ftp, aspera)
            }
        except IndexError:
            return None
