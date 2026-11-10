<#
.SYNOPSIS
  Fetch CC0 assets from Poly Haven into blender/vendor_cc0/<id>/ and list them in blender/vendor_cc0/MANIFEST.md.
  tools/blender_fetch_cc0.ps1 -Models a,b,c [-Textures x,y] [-Alphas a,b] [-Res 1k]
.DESCRIPTION
  Art v7 (D-205). For each id: a NEW folder of its own (an existing one is skipped, never overwritten); models as glTF
  (data only: the .gltf, its .bin and its textures; never a .blend), textures as the Diffuse map in PNG; every file's size
  and MD5 checked against the API's own listing; a section appended to the manifest with each file's URL, SHA-256 and
  bytes. The raw files are git-ignored and never ship.
  Requests carry a generic client name and nothing of the project or its owner.
  Refuses (exit 3) beside another role's lock or want: it writes files by shell (nothing of mine runs beside UNITY's lock).
#>
param(
    [string[]]$Models = @(),
    [string[]]$Textures = @(),
    [string[]]$Alphas = @(),
    [string]$Res = '1k',
    [string]$UsedBy = 'B-258'
)
$repo = Split-Path -Parent $PSScriptRoot
$others = @(Get-ChildItem (Join-Path $repo 'coordination\locks') -File | Where-Object { ($_.Name -like 'heavy_*' -or $_.Name -like 'want_*') -and $_.Name -notlike '*_blender.lock' })
if ($others.Count -gt 0) { "ABORT: locks on file: $($others.Name -join ', ')"; exit 3 }
$ua = 'blender-asset-fetch/1.0'
$root = Join-Path $repo 'blender\vendor_cc0'
$manifest = Join-Path $root 'MANIFEST.md'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$bad = 0
foreach ($job in @(@{ kind = 'model'; ids = $Models }, @{ kind = 'texture'; ids = $Textures })) {
    foreach ($id in $job.ids) {
        $dir = Join-Path $root $id
        if (Test-Path $dir) { "$id : the folder exists already, skipped"; continue }
        try {
            $info = Invoke-RestMethod -Uri "https://api.polyhaven.com/info/$id" -UserAgent $ua -TimeoutSec 30
            $f = Invoke-RestMethod -Uri "https://api.polyhaven.com/files/$id" -UserAgent $ua -TimeoutSec 30
            $files = @()
            if ($job.kind -eq 'model') {
                $g = $f.gltf.$Res.gltf
                if ($null -eq $g) { "$id : no glTF at $Res, skipped"; $bad++; continue }
                $files += @{ rel = "$id.gltf"; url = $g.url; md5 = $g.md5; size = $g.size }
                foreach ($p in $g.include.PSObject.Properties) { $files += @{ rel = $p.Name; url = $p.Value.url; md5 = $p.Value.md5; size = $p.Value.size } }
            } else {
                $d = $f.Diffuse.$Res.png
                if ($null -eq $d) { "$id : no Diffuse PNG at $Res, skipped"; $bad++; continue }
                $files += @{ rel = "${id}_diff_$Res.png"; url = $d.url; md5 = $d.md5; size = $d.size }
            }
            New-Item -ItemType Directory -Force $dir | Out-Null
            $authors = ($info.authors.PSObject.Properties.Name) -join ', '
            $what = 'glTF'; if ($job.kind -ne 'model') { $what = 'the Diffuse map, PNG' }
            $text = "`n### ${id}: `"$($info.name)`" by $authors`nhttps://polyhaven.com/a/$id ; $what, $Res ; downloaded $(Get-Date -Format 'yyyy-MM-dd HH:mm') ; used by $UsedBy`n`n| File (under blender/vendor_cc0/$id/) | Bytes | SHA-256 | URL |`n|---|---|---|---|`n"
            $total = 0; $okAll = $true
            foreach ($x in $files) {
                $dst = Join-Path $dir ($x.rel -replace '/', '\')
                New-Item -ItemType Directory -Force (Split-Path -Parent $dst) | Out-Null
                Invoke-WebRequest -Uri $x.url -UserAgent $ua -OutFile $dst -TimeoutSec 600 -UseBasicParsing
                $len = (Get-Item $dst).Length
                $md5 = (Get-FileHash $dst -Algorithm MD5).Hash.ToLower()
                $sha = (Get-FileHash $dst -Algorithm SHA256).Hash.ToLower()
                if ($md5 -ne $x.md5 -or $len -ne $x.size) { $okAll = $false; "  MISMATCH $($x.rel): $len bytes, md5 $md5 (the API: $($x.size), $($x.md5))" }
                $total += $len
                $text += "| $($x.rel) | $len | $sha | $($x.url) |`n"
            }
            if (-not $okAll) { $bad++; "$id : A FILE DID NOT MATCH THE API'S LISTING: not listed in the manifest; look at blender/vendor_cc0/$id/"; continue }
            [System.IO.File]::AppendAllText($manifest, $text, $utf8)
            "$id : '$($info.name)' by $authors : $($files.Count) files, $([math]::Round($total / 1MB, 1)) MB, all matched; listed in MANIFEST.md"
        } catch { $bad++; "$id : FAILED $($_.Exception.Message)" }
    }
}
# -Alphas: Poly Haven's glTF does not list a plant's ALPHA map (the cut-out of its leaf cards: "Alpha", or "leaves_alpha"
# on a tree), so a fern or a grass imports as solid cards. Each such map is added as a NEW file to the asset's existing
# folder (textures/<its own name>; an existing file is never overwritten) with its own section in the manifest.
foreach ($id in $Alphas) {
    $dir = Join-Path $root $id
    if (-not (Test-Path $dir)) { "$id : no folder yet (fetch the model first), skipped"; $bad++; continue }
    try {
        $f = Invoke-RestMethod -Uri "https://api.polyhaven.com/files/$id" -UserAgent $ua -TimeoutSec 30
        $rows = ''; $n = 0
        foreach ($p in $f.PSObject.Properties) {
            if ($p.Name -notmatch '(?i)alpha') { continue }
            $d = $p.Value.$Res.png
            if ($null -eq $d) { continue }
            $name = [System.IO.Path]::GetFileName(([uri]$d.url).AbsolutePath)
            $dst = Join-Path $dir ("textures\" + $name)
            if (Test-Path $dst) { "$id : textures/$name exists already, skipped"; continue }
            New-Item -ItemType Directory -Force (Split-Path -Parent $dst) | Out-Null
            Invoke-WebRequest -Uri $d.url -UserAgent $ua -OutFile $dst -TimeoutSec 600 -UseBasicParsing
            $len = (Get-Item $dst).Length
            $md5 = (Get-FileHash $dst -Algorithm MD5).Hash.ToLower()
            $sha = (Get-FileHash $dst -Algorithm SHA256).Hash.ToLower()
            if ($md5 -ne $d.md5 -or $len -ne $d.size) {
                Remove-Item $dst -Force
                $bad++; "  MISMATCH textures/${name}: $len bytes, md5 $md5 (the API: $($d.size), $($d.md5)): removed, not listed"; continue
            }
            $rows += "| textures/$name | $len | $sha | $($d.url) |`n"; $n++
        }
        if ($n -gt 0) {
            $text = "`n### ${id}: its Alpha map (the cut-out of the leaf cards; not in the glTF's own file list)`nhttps://polyhaven.com/a/$id ; PNG, $Res ; downloaded $(Get-Date -Format 'yyyy-MM-dd HH:mm') ; used by $UsedBy`n`n| File (under blender/vendor_cc0/$id/) | Bytes | SHA-256 | URL |`n|---|---|---|---|`n" + $rows
            [System.IO.File]::AppendAllText($manifest, $text, $utf8)
            "$id : $n alpha map(s) added and listed in MANIFEST.md"
        } else { "$id : no new alpha map" }
    } catch { $bad++; "$id : FAILED $($_.Exception.Message)" }
}
if ($bad -gt 0) { exit 1 }
