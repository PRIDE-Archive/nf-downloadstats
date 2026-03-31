import os
import click
from typing import Optional

from log_file_analyzer import LogFileAnalyzer
from log_file_util import FileUtil
from parquet_analyzer import ParquetAnalyzer
from parquet_reader import ParquetReader
from report_stat import ReportStat


@click.command("get_log_files",
               short_help="get_log_files", )
@click.option(
    "-r",
    "--root_dir",
    help="root folder where all the log files are stored(i.e transfer_logs_privacy_ready)",
    required=True,
)
@click.option(
    "-o",
    "--output",
    help="all the tsv log file paths written to this file",
    required=True,
)
@click.option(
    "-p",
    "--protocols",
    help="List of File Download protocols as appeared in the file system (i.e. fasp-aspera/gridftp-globus/http/ftp)",
    required=True,
    type=str
)
@click.option(
    "-v",
    "--public",
    help="Public or/and private folder",
    required=True,
    type=str
)
def get_log_files(root_dir: str, output: str, protocols: str, public: str) -> str:
    protocol_list = protocols.split(",")
    public_list = public.split(",")
    fileutil = FileUtil()
    file_paths_list = fileutil.process_access_methods(root_dir, output, protocol_list, public_list)
    return file_paths_list


@click.command("process_log_file",
               short_help="process log_file", )
@click.option(
    "-f",
    "--tsvfilepath",
    help="all the tsv log file paths written to this file",
    required=True,
)
@click.option(
    "-o",
    "--output_parquet",
    help="parquet file path to write individual file",
    required=True,
)
@click.option(
    "-r",
    "--resource",
    help="List of identifiers(paths) in file URIs to identify resources from(Eg: /pride/data/archive)",
    required=True,
    type=str
)
@click.option(
    "-c",
    "--complete",
    help="File download status can be complete or incomplete",
    required=True,
    type=str
)
@click.option(
    "-b",
    "--batch",
    help="Batch size of the TVS file to read",
    required=False,
    type=int
)
@click.option(
    "-a",
    "--accession_pattern",
    help="Resource accession pattern as a regular expression(Eg: PRIDE accessions '^PXD\\d{6}$'",
    required=True,
    type=str
)
def process_log_file(
    tsvfilepath: str,
    output_parquet: str,
    resource: str,
    complete: str,
    batch: int,
    accession_pattern: str
) -> None:
    resource_list = resource.split(",")
    completeness_list = complete.split(",")
    accession_pattern_list = accession_pattern.split(",")
    fileutil = FileUtil()
    fileutil.process_log_file(tsvfilepath, output_parquet, resource_list, completeness_list, batch, accession_pattern_list)


@click.command("run_log_file_stat",
               short_help="Run Log file Statistics", )
@click.option(
    "-f",
    "--file",
    help="All the tsv log file paths written to this file",
    required=True,
    type=str
)
@click.option(
    "-o",
    "--output",
    help="Report on HTML",
    required=True,
    type=str
)
def run_log_file_stat(file: str, output: str) -> None:
    log_file_stat = LogFileAnalyzer()
    log_file_stat.run_log_file_stat(file, output)

@click.command(
    "read-parquet",
    short_help="Read a single parquet file",
)
@click.option(
    "--file",
    help="Single parquet file to read",
    required=True,
)
def read_parquet_files(file: str) -> None:
    from exceptions import ParquetReadError
    
    if os.path.exists(file):
        parquet_reader = ParquetReader(file)
        parquet_reader.read(file)
    else:
        raise ParquetReadError(
            f"Parquet file not found: {file}",
            parquet_path=file
        )


@click.command(
    "merge_parquet_files",
    short_help="Merge Parquet Files into a single file",
)
@click.option("-f",
              "--input_dir",
              required=True,
              )
@click.option("-m",
              "--output_parquet",
              required=True,
              )
@click.option("-p",
              "--profile",
              required=True,
              )
def merge_parquet_files(input_dir: str, output_parquet: str, profile: str) -> None:
    stat_parquet = ParquetAnalyzer()
    stat_parquet.merge_parquet_files(input_dir, output_parquet)


@click.command(
    "analyze_parquet_files",
    short_help="Get file counts from parquet files",
)
@click.option("-m",
              "--output_parquet",
              required=True,
              )
@click.option("-g",
              "--project_level_download_counts",
              required=True,
              )
@click.option("-s",
              "--file_level_download_counts",
              required=True,
              )
@click.option("-y",
              "--project_level_yearly_download_counts",
              required=True,
              )
@click.option("-t",
              "--project_level_top_download_counts",
              required=True,
              )
@click.option("-a",
              "--all_data",
              required=True,
              )
@click.option("-p",
              "--profile",
              required=True,
              )
def analyze_parquet_files(
    output_parquet: str,
    project_level_download_counts: str,
    file_level_download_counts: str,
    project_level_yearly_download_counts: str,
    project_level_top_download_counts: str,
    all_data: str,
    profile: str
) -> None:
    stat_parquet = ParquetAnalyzer()
    stat_parquet.analyze_parquet_files(
        output_parquet,
        project_level_download_counts,
        file_level_download_counts,
        project_level_yearly_download_counts,
        project_level_top_download_counts,
        all_data
    )


@click.command("run_file_download_stat",
               short_help="Run File Down Statistics", )
@click.option(
    "-f",
    "--file",
    help="Parquet file containing file download stats",
    required=True,
    type=str
)
@click.option(
    "-o",
    "--output",
    help="Report on HTML",
    required=True,
    type=str
)
@click.option(
    "-r",
    "--report_template",
    help="Report Template in HTML. This means each resources may have their own HTML report",
    required=True,
    type=str
)
@click.option(
    "-b",
    "--baseurl",
    help="Base Url of the resource to access projects",
    required=True,
    type=str
)
@click.option(
    "-c",
    "--report_copy_filepath",
    help="Report can be copied to another file path",
    required=True,
    type=str
)
@click.option(
    "-y",
    "--skipped_years",
    help="You can skip years specified for the statistics calculations",
    required=False,
    type=str
)
def run_file_download_stat(
    file: str,
    output: str,
    report_template: str,
    baseurl: str,
    report_copy_filepath: str,
    skipped_years: Optional[str]
) -> None:
    # Convert the comma-separated string to a list of integers
    skipped_years_list = list(map(int, skipped_years.split(","))) if skipped_years else []

    file_download_stat = ReportStat()
    file_download_stat.run_file_download_stat(file, output, report_template, baseurl, report_copy_filepath,
                                              skipped_years_list)


@click.group()
def main():
    pass


# =============== Features Used ===============

main.add_command(get_log_files)
main.add_command(run_log_file_stat)
main.add_command(process_log_file)
main.add_command(merge_parquet_files)
main.add_command(analyze_parquet_files)
main.add_command(run_file_download_stat)

# =============== Additional Features ===============

main.add_command(read_parquet_files)

if __name__ == "__main__":
    main()
