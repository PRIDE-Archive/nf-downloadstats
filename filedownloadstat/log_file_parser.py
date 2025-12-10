import gzip
import re
from datetime import datetime
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="dask.dataframe")


class LogFileParser:
    """
    Class to parse the log file into parquet format
    eg: 2024-01-01T02:26:59.000Z\tebea3f4b11d3388b6da48148eb3a39a577bdc4bf\t179163579\t/pride/data/archive/2023/03/PXD034241/20210205_QExHFX3_RSLC10_Feng_Heckmann_EXT_onbead_dig_30_per_sample_turbo_nobio_S3_5.raw\tOUT\t03dbae9a96db63fa62487cd3c134d05230858127\tPartial\tChina\tShaanxi\tXi'an\t34.3287,109.0337\thttp\tpublic
    """

    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    def __init__(self, file_path, resource_list, completeness_list, accession_pattern_list):
        self.file_path = file_path
        self.RESOURCE_IDENTIFIERS = resource_list
        self.completeness = {c.lower().strip() for c in completeness_list}
        self.accession_pattern_list = accession_pattern_list

    def parse_gzipped_tsv(self, batch_size: int ):
        """
        Read the gzipped TSV file, parse each line, and yield data in batches.
        :param batch_size: Number of rows to include in each batch.
        :return: Generator that yields batches of parsed data.
        """
        batch = []
        try:
            with gzip.open(self.file_path, "rt", encoding="utf-8") as log_file:
                for line_no, line in enumerate(log_file, start=1):
                    line = line.replace('\\t', '\t')  # Replace literal '\t' with actual tab
                    row = line.strip().split('\t')  # Split each line by tab
                    parsed_line = self.parse_row(row, line_no)
                    if parsed_line:
                        batch.append(parsed_line)
                        # Yield the batch when it reaches the desired size
                        if len(batch) == batch_size:
                            yield batch
                            batch = []  # Reset the batch after yielding
                if batch:
                    yield batch
        except OSError as e:
            print(f"Skipping corrupted file: {self.file_path} due to {e}")
        except Exception as e:
            print(f"Got an exception while processing file {self.file_path}: {e}")

    def is_relevant_row(self, row):
        """
        Checks if the row matches the criteria based on resource identifiers and completeness.
        :param row: List of row values
        :return: Boolean indicating if the row is relevant
        """
        if  '/' in row[3]:

            if any(row[3].startswith(identifier) for identifier in self.RESOURCE_IDENTIFIERS):
                accession_field = self.get_accession(row[3])
                if accession_field is not None:
                    if row[3].split('/')[-1] is not None and row[3].split('/')[-1] != "":    # filename cannot be null
                        if  row[6].lower().strip() in self.completeness:
                            return True # all condition matched
                    else:
                        return False
                else:
                    return False

            else:
                return False
        else:
            return False

    def get_accession(self, path):
        """
        Searches for an accession number in the given path.

        Args:
            path (str): The file path to check.

        Returns:
            str or None: The matched accession number as a string, or None if no match is found.
        """
        try:
            for pattern in self.accession_pattern_list:
                corrected_pattern = re.sub(r"\\\\", r"\\", pattern)  # Fix escaping issues
                match = re.search(corrected_pattern, path)
                if match:
                    return match.group()
        except re.error as regex_err:
            print(f"Regex error: {regex_err} | Pattern: {pattern}")
        except Exception as e:
            print(f"Unexpected error in get_accession: {e}")

        return None  # No match found or an error occurred

    def parse_row(self, row, line_no):
        """
        Define a function to parse each row by extracting fields by column index
        :param row:
        :param line_no:
        :return:
        """
        if len(row) == 13:
            if self.is_relevant_row(row):
                try:
                    timestamp = self.clean_timestamp(row[0])
                    parsed_time = datetime.strptime(timestamp, self.DATETIME_FORMAT)

                    # Extract year, month, and date
                    year = parsed_time.year
                    month = parsed_time.month
                    date = parsed_time.date()

                    return {
                        "date": date,  # Date
                        "year": year,
                        "month": month,
                        "user": row[1].strip(),
                        "accession": self.get_accession(row[3]),  # Project accession of the resource(eg: PXD accession in PRIDE)
                        "filename": row[3].split('/')[-1],  # Files that are associate to a project(project acceesion)
                        "completed": row[6].lower().strip(),  # Completion Status (e.g., Complete or Incomplete)
                        "country": row[7],  # Country
                        "method": row[11],  # Method (e.g., ftp, aspera)
                        "timestamp": row[0].strip(),  # Original timestamp string
                        "geoip_region_name": self.clean_geoip_value(row[8]) if row[8] else "",  # GeoIP region name (e.g., Shaanxi)
                        "geoip_city_name": self.clean_geoip_value(row[9]) if row[9] else "",  # GeoIP city name (e.g., Xi'an)
                        "geo_location": row[10].strip() if row[10] else "",  # Geo location coordinates (e.g., 34.3287,109.0337)
                    }
                except IndexError as e:
                    print(f"Error processing line {line_no} with row {row}: {e}")
                    raise IndexError(f"IndexError: Row {line_no} with insufficient columns: {row}. Error: {e}")
            else:
                # print(f"Row not relevant at line {line_no}: {row}")
                return None
        else:
            print(f"WARNING: Expected 13 columns but found {len(row)} columns at line {line_no}. Row: {row}")
            return None

    @staticmethod
    def clean_timestamp(timestamp):
        """
        Cleans and adjusts the timestamp format for parsing.
        eg: 2024-09-13T23:58:17.000Z / 2024-09-14T07:14:07.419698061Z
        :param timestamp: Raw timestamp string
        :return: Cleaned timestamp string
        """
        if '.' in timestamp:
            timestamp = timestamp[:26] + 'Z'  # Trim to microseconds and re-add 'Z'
        return timestamp.rstrip('Z')  # Remove 'Z' for parsing

    @staticmethod
    def clean_geoip_value(value):
        """
        Cleans geoip values by filtering out placeholder strings.
        Handles cases like {geoip_region_name}, %{geoip_city_name}, etc.
        :param value: Raw geoip value string
        :return: Cleaned value or empty string if it's a placeholder
        """
        if not value:
            return ""
        value = value.strip()
        # Filter out placeholder patterns like {geoip_region_name}, %{geoip_city_name}, etc.
        if value.startswith('{') and value.endswith('}'):
            return ""  # Placeholder pattern like {geoip_region_name}
        if value.startswith('%{') and value.endswith('}'):
            return ""  # Placeholder pattern like %{geoip_city_name}
        return value
