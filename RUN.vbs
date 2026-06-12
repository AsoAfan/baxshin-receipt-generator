Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the script directory
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strDistDir = strScriptDir & "\dist"
strDBSource = strScriptDir & "\receipts.db"
strDBDest = strDistDir & "\receipts.db"

' Create dist folder if it doesn't exist
If Not objFSO.FolderExists(strDistDir) Then
    objFSO.CreateFolder(strDistDir)
End If

' Copy database to dist folder so app can access it
If objFSO.FileExists(strDBSource) Then
    On Error Resume Next
    objFSO.CopyFile strDBSource, strDBDest, True
    On Error Goto 0
End If

' Start the app silently in background
objShell.Run strDistDir & "\ReceiptApp.exe", 0, False

' Wait for app to start
WScript.Sleep 2000

' Open browser to localhost
objShell.Run "http://localhost", 0, False
