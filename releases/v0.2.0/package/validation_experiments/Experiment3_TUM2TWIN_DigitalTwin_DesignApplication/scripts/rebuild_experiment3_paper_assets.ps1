$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Rebuilding Experiment 3 paper-facing post-processing assets..."

function Invoke-PythonStep {
    param([string]$ScriptPath)
    Write-Host "python $ScriptPath"
    python $ScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw "Python step failed: $ScriptPath"
    }
}

# Base integrated matrix and audit shell.
Invoke-PythonStep "scripts\synthesize_final_integrated_paper_package.py"

# Addenda that extend the base matrix and evidence inventory.
Invoke-PythonStep "scripts\analyze_experiment3_effect_size_uncertainty.py"
Invoke-PythonStep "scripts\analyze_experiment3_directional_anisotropy.py"
Invoke-PythonStep "scripts\analyze_morphology_form_response_archetypes.py"
Invoke-PythonStep "scripts\synthesize_experiment3_addendum_key_result_rows.py"
Invoke-PythonStep "scripts\analyze_morphology_stage_transition.py"
Invoke-PythonStep "scripts\analyze_morphology_directional_fingerprint.py"

# Manuscript-facing synthesis layers.
Invoke-PythonStep "scripts\synthesize_experiment3_manuscript_module.py"
Invoke-PythonStep "scripts\synthesize_experiment3_submission_assets.py"
Invoke-PythonStep "scripts\synthesize_experiment3_section_paper_draft.py"
Invoke-PythonStep "scripts\synthesize_fluidx3d_numerical_protocol_audit.py"
Invoke-PythonStep "scripts\synthesize_building_form_wind_mechanism.py"
Invoke-PythonStep "scripts\synthesize_experiment3_reviewer_reproducibility_pack.py"
Invoke-PythonStep "scripts\synthesize_experiment3_final_completeness_audit.py"

Write-Host "Experiment 3 paper-facing assets rebuilt."
