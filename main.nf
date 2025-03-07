/*
========================================================================================
                 FILE Download Statistics Workflow
========================================================================================
 @#### Authors
 Suresh Hewapathirana <sureshhewabi@gmail.com>
----------------------------------------------------------------------------------------
*/

/*
 * Define the default parameters
 */
params.root_dir=''
params.output_file='parsed_data.parquet'
params.log_file=''
params.api_endpoint_file_download_per_project=''
params.protocols=''


log.info """\
 ===================================================
  F I L E    D O W N L O A D    S T A T I S T I C S
 ===================================================


FOR DEVELOPERS USE

SessionId           : $workflow.sessionId
LaunchDir           : $workflow.launchDir
projectDir          : $workflow.projectDir
dataDir             : ${params.root_dir}
workDir             : $workflow.workDir
RunName             : $workflow.runName
Profile             : $workflow.profile
NextFlow version    : $nextflow.version
Nextflow location   : ${params.nextflow_location}
Date                : ${new java.util.Date()}
Protocols           : ${params.protocols}
Resource Identifiers: ${params.resource_identifiers}
Completeness        : ${params.completeness}
Public/Private      : ${params.public_private}
Report Template     : ${params.report_template}
Batch Size          : ${params.log_file_batch_size}
Resource Base URL   : ${params.resource_base_url}
Report copy location: ${params.report_copy_filepath}
Skipped Years       : ${params.skipped_years}
Accession Pattern   : ${params.accession_pattern}
chunk size for file : ${params.chunk_size}
Disable DB Update   : ${params.disable_db_update}
api_endpoint_file_downloads_per_project : ${params.api_endpoint_file_downloads_per_project}
api_endpoint_file_downloads_per_file    : ${params.api_endpoint_file_downloads_per_file}

 """

process get_log_files {

    label 'process_very_low'

    input:
    val root_dir

    output:
    path "file_list.txt"

    script:
    """
    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  get_log_files \
        --root_dir $root_dir \
        --output "file_list.txt" \
        --protocols "${params.protocols.join(',')}" \
        --public "${params.public_private.join(',')}"
    """
}

process run_log_file_stat{

    label 'process_very_low'

    input:
    val file_paths  // Input the file generated by get_log_files

    output:
    path "log_file_statistics.html"  // Output the visualizations as an HTML report

    script:
    """
    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  run_log_file_stat \
        --file ${file_paths} \
        --output "log_file_statistics.html"
    """
}

process process_log_file {

    label 'process_very_low'
    label 'error_retry_max' // try 30 times


    input:
    val file_path  // Each file object from the channel

    output:
    path "*.parquet",optional: true  // Output files with unique names

    script:
    """
    # Extract a unique identifier from the log file name
    filename=\$(basename ${file_path} .log.tsv.gz)
    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  process_log_file \
        -f ${file_path} \
        -o "\${filename}.parquet" \
        -r "${params.resource_identifiers.join(",")}" \
        -c "${params.completeness.join(",")}" \
        -b ${params.log_file_batch_size} \
        -a ${params.accession_pattern.join(",")} \
        > process_log_file.log 2>&1
    """
}

process merge_parquet_files {

    label 'process_low'
    label 'error_retry_medium'

    input:
    val all_parquet_files  // A comma-separated string of file paths

    output:
    path("output_parquet"), emit: output_parquet

    script:
    """
    # Write the file paths to a temporary file, because otherwise Argument list(file list) will be too long
    echo "${all_parquet_files.join('\n')}" > all_parquet_files_list.txt

    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  merge_parquet_files \
        --input_dir all_parquet_files_list.txt \
        --output_parquet "output_parquet" \
        --profile $workflow.profile
    """
}

process analyze_parquet_files {

    label 'error_retry_max'

    input:
    val output_parquet

    output:
    path("project_level_download_counts.json"), emit: project_level_download_counts
    path("file_level_download_counts.json"), emit: file_level_download_counts
    path("project_level_yearly_download_counts.json"), emit: project_level_yearly_download_counts
    path("project_level_top_download_counts.json"), emit: project_level_top_download_counts
    path("all_data.json"), emit: all_data

    script:
    """
    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  analyze_parquet_files \
        --output_parquet ${output_parquet} \
        --project_level_download_counts project_level_download_counts.json \
        --file_level_download_counts file_level_download_counts.json \
        --project_level_yearly_download_counts project_level_yearly_download_counts.json \
        --project_level_top_download_counts project_level_top_download_counts.json \
        --all_data all_data.json \
        --profile $workflow.profile
    """
}

process run_file_download_stat {

    label 'error_retry_medium'

    input:
    val output_parquet

    output:
    path "file_download_stat.html"  // Output the visualizations as an HTML report

    script:
    """
    python3 ${workflow.projectDir}/filedownloadstat/file_download_stat.py  run_file_download_stat \
        --file ${output_parquet} \
        --output "file_download_stat.html" \
        --report_template ${params.report_template} \
        --baseurl ${params.resource_base_url} \
        --report_copy_filepath ${params.report_copy_filepath} \
        --skipped_years "${params.skipped_years.join(',')}"
    """
}

process update_project_download_counts {

    label 'error_retry'

    input:
    path project_level_download_counts // The JSON file to upload

    output:
    path "upload_response_file_downloads_per_project.txt" // Capture the response from the server

    script:
    """
    curl --location --max-time 300 '${params.api_endpoint_file_downloads_per_project}' \
    --header '${params.api_endpoint_header}' \
    --form 'files=@\"${project_level_download_counts}\"' > upload_response_file_downloads_per_project.txt
    """
}

process update_project_yearly_download_counts {

    label 'error_retry'

    input:
    path project_level_yearly_download_counts // The JSON file to upload

    output:
    path "upload_response_file_downloads_YEARLY_per_project.txt" // Capture the response from the server

    script:
    """
    curl --location --max-time 300 '${params.api_endpoint_file_downloads_per_project}' \
    --header '${params.api_endpoint_header}' \
    --form 'files=@\"${project_level_yearly_download_counts}\"' > upload_response_file_downloads_YEARLY_per_project.txt
    """
}

process update_file_level_download_counts {

    label 'error_retry'

    input:
    path file_level_download_counts // The large JSON file to process

    script:
    """
    # Create directories for split files and responses
    mkdir -p split_files upload_responses

    # Initialize variables
    chunk_size=${params.chunk_size}  # Number of objects per chunk
    total_lines=\$(jq '. | length' ${file_level_download_counts})  # Total number of objects in JSON
    chunk_number=0
    start_index=0

    echo "=== STARTING PROCESS ==="
    echo "Total lines in input JSON: \$total_lines"
    echo "Chunk size: \$chunk_size"

    # Split the JSON file into chunks
    while [ \$start_index -lt \$total_lines ]; do
        end_index=\$((start_index + chunk_size))
        echo "Creating chunk \$chunk_number: Start index = \$start_index, End index = \$end_index"

        # Use jq to extract a chunk of JSON objects
        jq -c ". | .[\${start_index}:\${end_index}]" ${file_level_download_counts} > "split_files/part_\${chunk_number}.json"
        chunk_file="split_files/part_\${chunk_number}.json"

        # Check if the chunk file is valid and non-empty
        if [ -s "\$chunk_file" ]; then
            echo "Chunk file created: \$chunk_file (Size: \$(wc -c < "\$chunk_file") bytes)"
        else
            echo "Warning: Chunk file \$chunk_file is empty!"
        fi

        # Increment start index and chunk number
        start_index=\$((end_index))
        chunk_number=\$((chunk_number + 1))
    done

    echo "=== CHUNKING COMPLETED ==="
    echo "Total chunks created: \$chunk_number"
    echo "Files in split_files directory:"
    ls -lh split_files/

    # Process and upload each JSON file
    for part_file in split_files/*; do
        echo "Processing file: \$part_file (Size: \$(wc -c < "\$part_file") bytes)"

        # Upload the JSON file and capture the server response
        curl --location --max-time 300 '${params.api_endpoint_file_downloads_per_file}' \
             --header '${params.api_endpoint_header}' \
             --form "files=@\${part_file}" \
             > "upload_responses/\$(basename \${part_file})_response.txt"

        if [ \$? -eq 0 ]; then
            echo "Response saved to upload_responses/\$(basename \${part_file})_response.txt"
        else
            echo "Error: Upload failed for file \$part_file"
        fi
    done

    echo "=== UPLOAD COMPLETED ==="
    echo "Responses saved in upload_responses/ directory:"
    ls -lh upload_responses/
    """
}

workflow {
    // Step 1: Gather file names
    def root_dir = params.root_dir
    def file_paths = get_log_files(root_dir)

    // Step 2: Run statistics in parallel with processing log files
    def stats_file = run_log_file_stat(file_paths)

    file_paths
        .splitText()                // Split file_list.txt into individual lines
        .map { it.split('\t')[0].trim() }  // Split each line by tab and take the first column (file name)
        .set { file_path }          // Save the channel

    // Step 2: Process each log file and generate Parquet files
    def all_parquet_files = process_log_file(file_path)

    // Collect all parquet files into a single channel for analysis
    all_parquet_files
        .collect()                  // Collect all parquet files into a single list
        .set { parquet_file_list }  // Save the collected files as a new channel

    merge_parquet_files(parquet_file_list)

    // Step 3: Analyze Parquet files
    analyze_parquet_files(merge_parquet_files.out.output_parquet)

    // Step 4: Generate Statistics for file downloads
    run_file_download_stat(merge_parquet_files.out.output_parquet)

    // Step 5: Update project level downloads in MongoDB
     if (!params.disable_db_update) {
        update_project_download_counts(analyze_parquet_files.out.project_level_download_counts)
     } else {
        println "Skipping update_project_download_counts because disable_db_update=true"
    }

    // Step 6: Update project level YEARLY downloads in MongoDB
     if (!params.disable_db_update) {
        update_project_yearly_download_counts(analyze_parquet_files.out.project_level_yearly_download_counts)
     } else {
        println "Skipping update_project_yearly_download_counts because disable_db_update=true"
    }

    // Step 7: Update project level downloads in MongoDB
    if (!params.disable_db_update) {
        update_file_level_download_counts(analyze_parquet_files.out.file_level_download_counts)
    } else {
        println "Skipping update_file_level_download_counts because disable_db_update=true"
    }
}