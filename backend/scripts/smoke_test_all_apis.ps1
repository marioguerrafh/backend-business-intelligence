param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Email = "owner@acme.com",
    [string]$Password = "Owner@123",
    [string]$CompanyId = "cmp_acme",
    [string]$SourceSystem = "smoke_api",
    [string]$ReportJsonPath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

$results = New-Object System.Collections.Generic.List[object]
$startedAt = [DateTimeOffset]::UtcNow

if ([string]::IsNullOrWhiteSpace($ReportJsonPath)) {
    $timestamp = $startedAt.ToString("yyyyMMdd_HHmmss")
    $ReportJsonPath = "d:/Projetos/business-intelligence/backend/data/demo/nova_distribuidora/smoke_report_$timestamp.json"
}

function Add-Result {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [int]$Status,
        [string]$Outcome,
        [string]$Detail
    )

    $results.Add(
        [pscustomobject]@{
            endpoint = $Name
            method = $Method
            path = $Path
            status = $Status
            outcome = $Outcome
            detail = $Detail
        }
    ) | Out-Null
}

function Invoke-Api {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [int[]]$ExpectedStatuses,
        [object]$Body = $null,
        [hashtable]$Headers = @{},
        [switch]$Raw
    )

    $url = "$BaseUrl$Path"
    $statusCode = 0
    $responseBody = $null

    try {
        if ($Raw) {
            $response = Invoke-WebRequest -Method $Method -Uri $url -Headers $Headers -Body $Body -ContentType "application/json" -UseBasicParsing
            $statusCode = [int]$response.StatusCode
            $responseBody = if ($response.Content) { $response.Content | ConvertFrom-Json } else { $null }
        }
        else {
            if ($null -ne $Body) {
                $json = $Body | ConvertTo-Json -Depth 10
                $response = Invoke-WebRequest -Method $Method -Uri $url -Headers $Headers -Body $json -ContentType "application/json" -UseBasicParsing
            }
            else {
                $response = Invoke-WebRequest -Method $Method -Uri $url -Headers $Headers -UseBasicParsing
            }
            $statusCode = [int]$response.StatusCode
            $responseBody = if ($response.Content) {
                try { $response.Content | ConvertFrom-Json } catch { $response.Content }
            }
            else {
                $null
            }
        }

        if ($ExpectedStatuses -contains $statusCode) {
            Add-Result -Name $Name -Method $Method -Path $Path -Status $statusCode -Outcome "ok" -Detail "expected"
        }
        else {
            Add-Result -Name $Name -Method $Method -Path $Path -Status $statusCode -Outcome "fail" -Detail "unexpected status"
        }

        return [pscustomobject]@{ status = $statusCode; body = $responseBody }
    }
    catch {
        $statusCode = 0
        $detail = $_.Exception.Message
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $raw = $reader.ReadToEnd()
                $responseBody = if ($raw) { try { $raw | ConvertFrom-Json } catch { $raw } } else { $null }
            }
            catch {
                $responseBody = $null
            }
        }

        if ($ExpectedStatuses -contains $statusCode) {
            Add-Result -Name $Name -Method $Method -Path $Path -Status $statusCode -Outcome "ok" -Detail "expected handled error"
            return [pscustomobject]@{ status = $statusCode; body = $responseBody }
        }

        Add-Result -Name $Name -Method $Method -Path $Path -Status $statusCode -Outcome "fail" -Detail $detail
        return [pscustomobject]@{ status = $statusCode; body = $responseBody }
    }
}

function Invoke-ImportCsvMultipart {
    param(
        [string]$Token,
        [string]$Template,
        [string]$CsvContent,
        [int[]]$ExpectedStatuses
    )

    $name = "imports.csv ($Template)"
    $path = "/v1/imports/csv"
    $url = "$BaseUrl$path"

    $tmpFile = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -LiteralPath $tmpFile -Value $CsvContent -Encoding UTF8

        $handler = New-Object System.Net.Http.HttpClientHandler
        $client = New-Object System.Net.Http.HttpClient($handler)
        try {
            $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", $Token)
            $client.DefaultRequestHeaders.Add("X-Correlation-ID", "smoke-import-$(Get-Date -Format yyyyMMddHHmmss)")

            $multipart = New-Object System.Net.Http.MultipartFormDataContent
            try {
                $multipart.Add((New-Object System.Net.Http.StringContent($CompanyId)), "company_id") | Out-Null
                $multipart.Add((New-Object System.Net.Http.StringContent($Template)), "template") | Out-Null
                $multipart.Add((New-Object System.Net.Http.StringContent($SourceSystem)), "source_system") | Out-Null

                $bytes = [System.IO.File]::ReadAllBytes($tmpFile)
                $fileContent = New-Object System.Net.Http.ByteArrayContent (, $bytes)
                $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/csv")
                $multipart.Add($fileContent, "file", "$Template.csv") | Out-Null

                $httpResponse = $client.PostAsync($url, $multipart).GetAwaiter().GetResult()
                $status = [int]$httpResponse.StatusCode
                $raw = $httpResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
                $body = if ($raw) { try { $raw | ConvertFrom-Json } catch { $raw } } else { $null }

                if ($ExpectedStatuses -contains $status) {
                    Add-Result -Name $name -Method "POST" -Path $path -Status $status -Outcome "ok" -Detail "expected"
                }
                else {
                    Add-Result -Name $name -Method "POST" -Path $path -Status $status -Outcome "fail" -Detail "unexpected status"
                }

                return [pscustomobject]@{ status = $status; body = $body }
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
    finally {
        Remove-Item -LiteralPath $tmpFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Running smoke test for all exposed APIs..."

# 1) Base health
Invoke-Api -Name "platform.health" -Method "GET" -Path "/health" -ExpectedStatuses @(200) | Out-Null

# 2) Module health endpoints
$healthPaths = @(
    "/v1/company/health",
    "/v1/imports/health",
    "/v1/kpi/health",
    "/v1/alert/health",
    "/v1/insight/health",
    "/v1/recommendation/health",
    "/v1/ai/health",
    "/v1/notification/health",
    "/v1/omie/health"
)
foreach ($hp in $healthPaths) {
    Invoke-Api -Name "module.health" -Method "GET" -Path $hp -ExpectedStatuses @(200) | Out-Null
}

# 3) Auth flow
$login = Invoke-Api -Name "auth.login" -Method "POST" -Path "/v1/auth/login" -ExpectedStatuses @(200) -Body @{
    email = $Email
    password = $Password
    company_id = $CompanyId
}

if ($login.status -ne 200 -or -not $login.body.access_token) {
    throw "auth.login failed; cannot continue smoke test."
}

$accessToken = [string]$login.body.access_token
$refreshToken = [string]$login.body.refresh_token
$authHeaders = @{ Authorization = "Bearer $accessToken" }

Invoke-Api -Name "auth.me" -Method "GET" -Path "/v1/auth/me" -ExpectedStatuses @(200) -Headers $authHeaders | Out-Null
Invoke-Api -Name "auth.users" -Method "GET" -Path "/v1/auth/users" -ExpectedStatuses @(200) -Headers $authHeaders | Out-Null

$refresh = Invoke-Api -Name "auth.refresh" -Method "POST" -Path "/v1/auth/refresh" -ExpectedStatuses @(200) -Body @{
    refresh_token = $refreshToken
}
if ($refresh.status -eq 200 -and $refresh.body.access_token) {
    $accessToken = [string]$refresh.body.access_token
    $refreshToken = [string]$refresh.body.refresh_token
    $authHeaders = @{ Authorization = "Bearer $accessToken" }
}

# 4) Business customer create/get
$seed = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$customerPayload = @{
    company_id = $CompanyId
    legal_name = "Smoke Cliente $seed Ltda"
    trade_name = "Smoke Cliente $seed"
    document_number = "99999999$seed"
    status = "active"
    billing_address = @{
        street = "Rua Teste"
        number = "100"
        district = "Centro"
        city = "Campinas"
        state = "SP"
        country = "Brasil"
        postal_code = "13000000"
    }
    contacts = @(
        @{ channel_type = "email"; value = "smoke$seed@cliente.com" }
    )
    external_refs = @(
        @{ source_system = $SourceSystem; external_id = "SMK-CUST-$seed" }
    )
    source_system = $SourceSystem
    source_record_id = "SMK-CUST-REC-$seed"
    canonical_schema_version = "1.0"
}

$customerCreate = Invoke-Api -Name "business.customers.create" -Method "POST" -Path "/v1/business/customers" -ExpectedStatuses @(200) -Headers $authHeaders -Body $customerPayload
if ($customerCreate.status -eq 200 -and $customerCreate.body.customer_id) {
    $cid = [string]$customerCreate.body.customer_id
    Invoke-Api -Name "business.customers.get" -Method "GET" -Path "/v1/business/customers/$CompanyId/$cid" -ExpectedStatuses @(200) -Headers $authHeaders | Out-Null
}

# 5) Business product create/get
$productPayload = @{
    company_id = $CompanyId
    sku = "SMK-SKU-$seed"
    name = "Smoke Produto $seed"
    category = "Teste"
    unit_of_measure = "UN"
    status = "active"
    default_cost = 10.5
    default_price = 15.9
    tax_profile_ref = "ICMS18"
    external_refs = @(
        @{ source_system = $SourceSystem; external_id = "SMK-PRD-$seed" }
    )
    source_system = $SourceSystem
    source_record_id = "SMK-PRD-REC-$seed"
    canonical_schema_version = "1.0"
}

$productCreate = Invoke-Api -Name "business.products.create" -Method "POST" -Path "/v1/business/products" -ExpectedStatuses @(200) -Headers $authHeaders -Body $productPayload
if ($productCreate.status -eq 200 -and $productCreate.body.product_id) {
    $productId = [string]$productCreate.body.product_id
    Invoke-Api -Name "business.products.get" -Method "GET" -Path "/v1/business/products/$CompanyId/$productId" -ExpectedStatuses @(200) -Headers $authHeaders | Out-Null
}

# 6) Imports endpoint (CSV multipart)
$financialCsv = @"
source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,cash_out_amount,operating_cash_flow_amount,description
SMOKE-FIN-$seed,2026-07-10,operating,bank,1000.00,150.00,850.00,Lancamento smoke test
"@
Invoke-ImportCsvMultipart -Token $accessToken -Template "financial" -CsvContent $financialCsv -ExpectedStatuses @(200) | Out-Null

# 7) Summary endpoint
Invoke-Api -Name "summary.get" -Method "GET" -Path "/v1/summary?company_id=$CompanyId" -ExpectedStatuses @(200,404) -Headers $authHeaders | Out-Null

# 8) KPI formula evaluate
$kpiPayload = @{
    formula_id = "f.net_revenue"
    company_id = $CompanyId
    period_ref = "2026-07"
    metrics = @{
        gross_revenue = @(1000, 900)
        tax_amount = @(180, 160)
        return_amount = @(10, 12)
        discount_amount = @(20, 15)
    }
}
Invoke-Api -Name "kpi.evaluate_formula" -Method "POST" -Path "/v1/kpi/internal/formulas/evaluate" -ExpectedStatuses @(200) -Body $kpiPayload | Out-Null

# 9) Logout
Invoke-Api -Name "auth.logout" -Method "POST" -Path "/v1/auth/logout" -ExpectedStatuses @(204) -Body @{ refresh_token = $refreshToken } | Out-Null

Write-Host ""
Write-Host "Smoke test summary:"
$results | Format-Table -AutoSize

$finishedAt = [DateTimeOffset]::UtcNow
$totalCount = $results.Count
$okCount = @($results | Where-Object { $_.outcome -eq "ok" }).Count
$failCount = @($results | Where-Object { $_.outcome -eq "fail" }).Count

$resultItems = @(
    $results | ForEach-Object {
        [ordered]@{
            endpoint = $_.endpoint
            method = $_.method
            path = $_.path
            status = $_.status
            outcome = $_.outcome
            detail = $_.detail
        }
    }
)

$report = [ordered]@{
    generated_at_utc = $finishedAt.ToString("o")
    started_at_utc = $startedAt.ToString("o")
    duration_seconds = [Math]::Round(($finishedAt - $startedAt).TotalSeconds, 3)
    base_url = $BaseUrl
    company_id = $CompanyId
    summary = [ordered]@{
        total = $totalCount
        ok = $okCount
        fail = $failCount
        success = ($failCount -eq 0)
    }
    results = $resultItems
}

$reportDir = Split-Path -Path $ReportJsonPath -Parent
if (-not [string]::IsNullOrWhiteSpace($reportDir)) {
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReportJsonPath -Encoding UTF8
Write-Host "JSON report written to: $ReportJsonPath"

$fails = @($results | Where-Object { $_.outcome -eq "fail" })
if ($fails.Count -gt 0) {
    Write-Host ""
    Write-Warning "Smoke test finished with failures: $($fails.Count)"
    exit 1
}

Write-Host ""
Write-Host "Smoke test finished successfully."
