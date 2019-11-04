#@echo off
Write-Output "                               ZCC connectivity tool                  "
Write-Output "                                     Version 1                                  "
Write-Output ""
do{
    try{
    [ipaddress]$Zcc= read-host 'ZCC IP'
    } catch {
    Write-Output "Invalid IP Address"
    }#catch
}#do
while($zcc -eq $null)

do{
    try{
        [int]$Pings= Read-Host 'Amount of pings'
    }#try
    catch{
        write-output "Must be an integer"
    }#catch
}#do
while($pings -eq $null)

#$startTime = Get-Date
function Using_SSH_Key{
    Write-Output Uploading
    ..\pscp.exe -i ..\Secrets\ssh.ppk pynatz4.py root@"$zcc":/root/
    Write-Output Running...
    ..\plink.exe -i ..\Secrets\ssh.ppk root@"$zcc" "chmod 001 pynatz4.py; ./pynatz4.py "$pings"" | Tee-Object -FilePath "Connectivity test output.txt"
    #..\plink.exe -i ..\Secrets\ssh.ppk root@"$zcc" "./pynatz4.py "$pings"" | Tee-Object -FilePath "Connectivity test output.txt"
}

function No_SSH_Key{
    Write-Output Uploading
    ..\pscp.exe -batch -pw "$password" pynatz4.py root@"$zcc":/root/
    #$wshell = New-Object -ComObject wscript.shell;
    #$wshell.AppActivate('title of the application window')
    #Sleep 1
    #$wshell.SendKeys('~')
    #$antispoof = '..\plink.exe -pw "$password" root@"$zcc" "chmod 001 pynatz2.py" 2>&1 $error'
    #$LASTEXITCODE
    #if $LASTEXITCODE -ne 0){
    #write-host "Running..."
    ..\plink.exe -batch -pw "$password" root@"$zcc" "chmod 001 pynatz4.py; ./pynatz4.py "$pings"" | Tee-Object -FilePath "Connectivity test output.txt"
    #..\plink.exe -pw "$password" root@"$zcc" "./pynatz2.py "$pings"" | Tee-Object -FilePath "Connectivity test output.txt"
}


###$endtime = Get-Date
###Write-host "Run time is $(($endtime - $startTime).totalseconds) seconds" 

$notSelected = $true
do{
    $IsSSH = Read-Host 'Are you using an SSH Key? [Y/N]'
    if ($IsSSH.ToLower() -eq 'y') {
        Using_SSH_Key; $notSelected = $false
    }#if
    elseif ($IsSSH.ToLower() -eq 'n'){
        $Password = Read-Host 'ZCC password' -AsSecureString
        $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
        $ErrorActionPreference = "Stop"
        No_SSH_Key ; $notSelected = $false
    }#elseif
}#do 
while($notSelected)

pause
