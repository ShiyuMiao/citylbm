$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$manifest = Join-Path $root "manifests\tum2twin_gitlab_tree_blobs.csv"
$destRoot = "D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_full_lod2"
$outCsv = Join-Path $root "manifests\full_lod2_download_manifest.csv"
$base = "https://gitlab.lrz.de/tum-gis/tum2twin-datasets/-/raw/main"

$rows = Import-Csv $manifest | Where-Object { $_.path -like "citygml/lod2-building-datasets/*.gml" }
$results = @()

foreach ($row in $rows) {
    $rel = $row.path
    $url = "$base/$rel"
    $out = Join-Path $destRoot $rel
    New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null

    $needsDownload = $true
    if (Test-Path $out) {
        if ((Get-Item $out).Length -gt 1024) {
            $needsDownload = $false
        }
    }

    if ($needsDownload) {
        Write-Host "Downloading $rel"
        & C:\Windows\System32\curl.exe -L --retry 5 --retry-delay 3 --retry-all-errors -o $out $url
        if ($LASTEXITCODE -ne 0) {
            throw "curl failed for $rel with exit code $LASTEXITCODE"
        }
    } else {
        Write-Host "SKIP $rel"
    }

    $item = Get-Item $out
    $results += [pscustomobject]@{
        path = $out
        source_url = $url
        size_bytes = $item.Length
        md5 = (Get-FileHash -Algorithm MD5 $out).Hash.ToLower()
        sha256 = (Get-FileHash -Algorithm SHA256 $out).Hash.ToLower()
        download_time_local = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        license = "repository LICENSE, verify before publication"
        citation = "TUM2TWIN GitLab dataset repository"
        evidence_type = "newly_run"
    }
}

$results | Export-Csv -NoTypeInformation -Encoding UTF8 $outCsv
$results | Format-Table -AutoSize
