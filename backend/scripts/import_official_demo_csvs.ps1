param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Email = "owner@acme.com",
    [string]$Password = "Owner@123",
    [string]$CompanyId = "cmp_acme",
    [string]$SourceSystem = "csv_manual",
    [string]$DataDir = "d:/Projetos/business-intelligence/backend/data/demo/nova_distribuidora",
    [string]$CorrelationPrefix = "imp-demo",
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

# Required for Windows PowerShell 5.1 to resolve HttpClient types.
Add-Type -AssemblyName System.Net.Http

function Test-FileExists {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "File not found: $Path"
    }
}

function Get-AccessToken {
    param(
        [string]$ApiBaseUrl,
        [string]$LoginEmail,
        [string]$LoginPassword,
        [string]$TenantCompanyId
    )

    $loginPayload = @{
        email = $LoginEmail
        password = $LoginPassword
        company_id = $TenantCompanyId
    } | ConvertTo-Json

    $loginUrl = "$ApiBaseUrl/v1/auth/login"
    $response = Invoke-RestMethod -Method Post -Uri $loginUrl -ContentType "application/json" -Body $loginPayload

    if (-not $response.access_token) {
        throw "Login succeeded but no access_token was returned."
    }

    return [string]$response.access_token
}

function New-MultipartResponse {
    param(
        [string]$ApiBaseUrl,
        [string]$Token,
        [string]$Company,
        [string]$Template,
        [string]$Source,
        [string]$FilePath,
        [string]$CorrelationId
    )

    $url = "$ApiBaseUrl/v1/imports/csv"

    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    try {
        $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", $Token)
        $client.DefaultRequestHeaders.Add("X-Correlation-ID", $CorrelationId)

        $multipart = New-Object System.Net.Http.MultipartFormDataContent
        try {
            $companyContent = New-Object System.Net.Http.StringContent($Company)
            $templateContent = New-Object System.Net.Http.StringContent($Template)
            $sourceContent = New-Object System.Net.Http.StringContent($Source)
            $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
            # Unary comma forces PowerShell to pass the byte[] as a single constructor argument.
            $byteContent = New-Object System.Net.Http.ByteArrayContent (, $fileBytes)
            $byteContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/csv")

            $null = $multipart.Add($companyContent, "company_id")
            $null = $multipart.Add($templateContent, "template")
            $null = $multipart.Add($sourceContent, "source_system")
            $null = $multipart.Add($byteContent, "file", [System.IO.Path]::GetFileName($FilePath))

            return $client.PostAsync($url, $multipart).GetAwaiter().GetResult()
        }
        finally {
            $multipart.Dispose()
        }
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

function Invoke-CsvImport {
    param(
        [string]$ApiBaseUrl,
        [string]$Token,
        [string]$Company,
        [string]$Template,
        [string]$Source,
        [string]$FilePath,
        [string]$CorrelationId
    )

    $httpResponse = New-MultipartResponse -ApiBaseUrl $ApiBaseUrl -Token $Token -Company $Company -Template $Template -Source $Source -FilePath $FilePath -CorrelationId $CorrelationId
    $statusCode = [int]$httpResponse.StatusCode
    $rawBody = $httpResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()

    $jsonBody = $null
    if (-not [string]::IsNullOrWhiteSpace($rawBody)) {
        try {
            $jsonBody = $rawBody | ConvertFrom-Json
        }
        catch {
            $jsonBody = $null
        }
    }

    return [pscustomobject]@{
        Template = $Template
        File = [System.IO.Path]::GetFileName($FilePath)
        HttpStatus = $statusCode
        Body = $jsonBody
        RawBody = $rawBody
        CorrelationId = $CorrelationId
    }
}

if (-not $SkipHealthCheck) {
    $healthUrl = "$BaseUrl/v1/imports/health"
    $health = Invoke-RestMethod -Method Get -Uri $healthUrl
    if ($health.status -ne "ok") {
        throw "Imports module health check failed at $healthUrl"
    }
}

$customersFile = Join-Path $DataDir "customers.csv"
$productsFile = Join-Path $DataDir "products.csv"
$salesFile = Join-Path $DataDir "sales.csv"
$financialFile = Join-Path $DataDir "financial.csv"

Test-FileExists -Path $customersFile
Test-FileExists -Path $productsFile
Test-FileExists -Path $salesFile
Test-FileExists -Path $financialFile

Write-Host "Logging in to API..."
$token = Get-AccessToken -ApiBaseUrl $BaseUrl -LoginEmail $Email -LoginPassword $Password -TenantCompanyId $CompanyId

$imports = @(
    @{ template = "customers"; file = $customersFile }
    @{ template = "products"; file = $productsFile }
    @{ template = "sales"; file = $salesFile }
    @{ template = "financial"; file = $financialFile }
)

$results = New-Object System.Collections.Generic.List[object]

for ($i = 0; $i -lt $imports.Count; $i++) {
    $item = $imports[$i]
    $corr = "$CorrelationPrefix-$($i + 1)"

    Write-Host "Importing $($item.template) from $($item.file)..."
    $result = Invoke-CsvImport -ApiBaseUrl $BaseUrl -Token $token -Company $CompanyId -Template $item.template -Source $SourceSystem -FilePath $item.file -CorrelationId $corr
    $results.Add($result)

    if ($result.HttpStatus -ge 400) {
        Write-Warning "Import failed for template '$($item.template)' (HTTP $($result.HttpStatus))."
        continue
    }

    $status = if ($result.Body) { $result.Body.status } else { "unknown" }
    $imported = if ($result.Body) { $result.Body.imported_rows } else { 0 }
    $failed = if ($result.Body) { $result.Body.failed_rows } else { 0 }
    Write-Host " -> status=$status imported=$imported failed=$failed"
}

Write-Host ""
Write-Host "Import summary:"
$summary = foreach ($r in $results) {
    [pscustomobject]@{
        template = $r.Template
        file = $r.File
        http_status = $r.HttpStatus
        status = if ($r.Body) { $r.Body.status } else { "error" }
        total_rows = if ($r.Body) { $r.Body.total_rows } else { $null }
        imported_rows = if ($r.Body) { $r.Body.imported_rows } else { $null }
        failed_rows = if ($r.Body) { $r.Body.failed_rows } else { $null }
        ingest_event_id = if ($r.Body) { $r.Body.ingest_event_id } else { $null }
        inconsistencies = if ($r.Body -and $r.Body.inconsistencies) { $r.Body.inconsistencies.Count } else { 0 }
        correlation_id = $r.CorrelationId
    }
}

$summary | Format-Table -AutoSize

$failedImports = $summary | Where-Object { $_.http_status -ge 400 -or $_.status -eq "failed" }
if ($failedImports.Count -gt 0) {
    Write-Host ""
    Write-Warning "One or more imports failed or completed with status=failed."
    foreach ($fi in $failedImports) {
        $raw = ($results | Where-Object { $_.Template -eq $fi.template } | Select-Object -First 1).RawBody
        Write-Host ""
        Write-Host "Template: $($fi.template)"
        Write-Host "HTTP: $($fi.http_status)"
        Write-Host "Body: $raw"
    }
    exit 1
}

Write-Host ""
Write-Host "All official CSV imports completed successfully."
