[CmdletBinding()]
param(
  [switch]$Upload,
  [switch]$LicenseConfirmed,
  [string]$SourceRoot = "$env:USERPROFILE\NQTickResearch\github_releases_upload\Sealed"
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = 'rgentil2/NQ-Ticks-Dev-2026'
if ($Upload -and -not $LicenseConfirmed) { throw 'Debe confirmar los permisos de licencia con -LicenseConfirmed.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Se requiere GitHub CLI (gh).' }
$isPrivate = (& gh repo view $repo --json isPrivate --jq '.isPrivate' | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $isPrivate -ne 'true') { throw 'El repositorio DEV debe ser privado y accesible.' }
$releaseJson = (& gh release list --repo $repo --limit 100 --json tagName | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'No se pudo listar Releases.' }
$known = @()
if ($releaseJson.Trim()) {
    foreach ($r in @((ConvertFrom-Json -InputObject $releaseJson))) {
        if ($null -ne $r -and $r.PSObject.Properties.Name -contains 'tagName') { $known += [string]$r.tagName }
    }
}
$totalAssets = 0
# EXPLICIT WHITELIST: never touch 2026-07 to 2026-09.
foreach ($month in @('2025-10','2025-11','2025-12')) {
    $dir = Join-Path $SourceRoot $month
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "No existe: $dir" }
    $assets = @()
    foreach ($kind in @('Last','Bid','Ask')) {
        $name = 'NQ_' + $month + '_' + $kind + '.7z'
        $data = Join-Path $dir ($name + '.001')
        $sum = Join-Path $dir ($name + '.sha256')
        if (-not (Test-Path -LiteralPath $data) -or -not (Test-Path -LiteralPath $sum)) {
            throw "Faltan archivos: $name"
        }
        $checksum = Get-Content -LiteralPath $sum -Raw
        if ($checksum -notmatch '(?i)\b[0-9a-f]{64}\b') { throw "SHA-256 incorrecto: $sum" }
        $expected = $Matches[0].ToLowerInvariant()
        $actual = (Get-FileHash -LiteralPath $data -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) { throw "Hash distinto: $data" }
        $assets += Get-Item -LiteralPath $data
        $assets += Get-Item -LiteralPath $sum
    }
    $totalAssets += $assets.Count
    Write-Host "VERIFICADO $month ($($assets.Count) adjuntos)."
    if (-not $Upload) { continue }

    $tag = 'nq-tick-' + $month
    if ($known -notcontains $tag) {
        & gh release create $tag --repo $repo --title "NQ Tick $month DEV" --notes "Solo Q4 2025 Last/Bid/Ask para nuevo estudio NQ; no incluye holdout de 2026." | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear $tag" }
        $known += $tag
    }
    $json = (& gh release view $tag --repo $repo --json assets | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar $tag" }
    $remote = @()
    $object = ConvertFrom-Json -InputObject $json
    if ($null -ne $object -and $null -ne $object.assets) { $remote = @($object.assets) }
    foreach ($file in $assets) {
        $matched = @($remote | Where-Object { $_.name -eq $file.Name })
        if ($matched.Count) {
            if ([long]$matched[0].size -ne [long]$file.Length) {
                throw "El tamaño remoto difiere para $($file.Name)"
            }
            Write-Host "YA EXISTE: $($file.Name)"
            continue
        }
        Write-Host "SUBIENDO: $($file.Name)"
        & gh release upload $tag $file.FullName --repo $repo | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "Fallo al subir: $($file.Name)" }
    }
}
Write-Host "TERMINADO. Meses=3, adjuntos comprobados=$totalAssets, Upload=$Upload. NO se tocó Sealed."
