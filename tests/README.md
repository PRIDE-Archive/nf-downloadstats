# Test Suite Documentation

This directory contains comprehensive unit and integration tests for the file download statistics pipeline.

## Test Structure

### Unit Tests

- **`test_log_parser.py`** - Tests for LogFileParser class (existing, updated)
- **`test_log_parser_extended.py`** - Extended tests for new fields and error handling
- **`test_parquet_writer.py`** - Tests for ParquetWriter class
- **`test_parquet_reader.py`** - Tests for ParquetReader class
- **`test_parquet_analyzer.py`** - Tests for ParquetAnalyzer class
- **`test_log_file_util.py`** - Tests for FileUtil class
- **`test_slack_pusher.py`** - Tests for SlackPusher class
- **`test_exceptions.py`** - Tests for custom exception classes

### Integration Tests

- **`test_integration.py`** - Integration tests for critical workflows:
  - Complete log file to parquet workflow
  - Parquet analysis workflow
  - Merging multiple parquet files
  - Error handling across modules

## Running Tests

### Run all tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Run specific test file
```bash
python -m unittest tests.test_log_parser
```

### Run with verbose output
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run with coverage
```bash
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report
coverage html  # Generate HTML report
```

## Test Coverage

The test suite covers:

1. **Log File Parsing**
   - Valid row parsing
   - Invalid row handling
   - New fields (timestamp, geoip_region_name, geoip_city_name, geo_location)
   - Placeholder value filtering
   - Error recovery

2. **Parquet Operations**
   - Writing parquet files
   - Reading parquet files
   - Merging parquet files
   - Schema validation
   - Error handling

3. **Data Analysis**
   - Project-level counts
   - File-level counts
   - Yearly counts
   - Top downloads
   - Full data export

4. **Error Handling**
   - Custom exception classes
   - Error propagation
   - Recovery strategies
   - Validation errors

5. **Integration Workflows**
   - End-to-end log processing
   - Multi-file processing
   - Error recovery in workflows

## Adding New Tests

When adding new functionality:

1. Add unit tests for the new module/class
2. Add integration tests if it affects workflows
3. Update this README if adding new test categories
4. Ensure tests follow the existing patterns (unittest framework)

## Test Fixtures

Tests use temporary directories and files that are automatically cleaned up. No permanent files are created during testing.

