param(
  [string]$PgSuperUser = "postgres",
  [string]$PgSuperPassword = "postgres",
  [string]$DbName = "shop_db",
  [string]$DbUser = "shop_user",
  [string]$DbPassword = "shop_pass",
  [string]$Host = "localhost",
  [int]$Port = 5432
)

$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
if (-not (Test-Path $psql)) {
  Write-Error "psql �� ������ �� ���� $psql. �������� PostgreSQL Server."
  exit 1
}

$env:PGPASSWORD = $PgSuperPassword

try {
  $roleExists = & $psql -h $Host -p $Port -U $PgSuperUser -d postgres -t -A -c "SELECT 1 FROM pg_roles WHERE rolname='$DbUser';"
  if (-not $roleExists) {
    & $psql -h $Host -p $Port -U $PgSuperUser -d postgres -c "CREATE ROLE $DbUser LOGIN PASSWORD '$DbPassword';"
    if ($LASTEXITCODE -ne 0) { throw "�� ������� ������� ���� $DbUser" }
    Write-Host "������� ���� $DbUser"
  } else {
    & $psql -h $Host -p $Port -U $PgSuperUser -d postgres -c "ALTER ROLE $DbUser WITH LOGIN PASSWORD '$DbPassword';"
    if ($LASTEXITCODE -ne 0) { throw "�� ������� �������� ������ ���� $DbUser" }
    Write-Host "���� $DbUser ��� ������������, ������ ��������"
  }

  $dbExists = & $psql -h $Host -p $Port -U $PgSuperUser -d postgres -t -A -c "SELECT 1 FROM pg_database WHERE datname='$DbName';"
  if (-not $dbExists) {
    & $psql -h $Host -p $Port -U $PgSuperUser -d postgres -c "CREATE DATABASE $DbName OWNER $DbUser;"
    if ($LASTEXITCODE -ne 0) { throw "�� ������� ������� �� $DbName" }
    Write-Host "������� �� $DbName"
  } else {
    Write-Host "�� $DbName ��� ����������"
  }

  Write-Host "������. ������ ����� ��������� migrate/seed_demo."
}
finally {
  Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
