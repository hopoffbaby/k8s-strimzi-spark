# Define the base path to your YAML template
$templatePath = "spark-pi.yaml"

# Loop to create and submit the configuration 5 times with different names
1..5 | ForEach-Object {
    $newName = "spark-pi-$($_)"  # Generate new name based on loop counter
    $newFilePath = "spark-$newName.yaml"  # Define path for the modified file
    
    # Read the template content
    $yamlContent = Get-Content -Path $templatePath -Raw
    
    # Replace the name in the YAML content
    $modifiedContent = $yamlContent -replace 'name: spark-pi-1', "name: $newName"
    
    # Write the modified content to a new YAML file
    $modifiedContent | Out-File -FilePath $newFilePath
    
    # Apply the new YAML file with kubectl
    kubectl apply -f $newFilePath

    # Output the name of the file applied
    Write-Host "Applied configuration for $newName"
    Remove-Item -Path "spark-$newName.yaml" -Force
}

# Clean up

Write-Host "Temporary files removed."
