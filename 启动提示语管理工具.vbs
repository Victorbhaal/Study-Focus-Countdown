' 启动提示语管理工具.vbs
' =======================
' 双击本文件即可静默启动“学习倒计时提示语管理工具”(无控制台窗口)。
' 本启动器与工具(.pyw)需在同一文件夹根目录下。它会自动定位同目录下
' 含有 TIPS_TOOL_MARKER 标记的 .pyw，再用 pythonw.exe 运行它。
' 需要系统 PATH 中存在 pythonw.exe（标准 Python 安装会自带）。

Option Explicit

Dim fso, dir, folder, file, target, ts, head, sh, foundMarker

Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
target = ""
foundMarker = "TIPS_TOOL_MARKER"

On Error Resume Next
Set folder = fso.GetFolder(dir)
If Err.Number <> 0 Then
  MsgBox "无法访问当前文件夹：" & dir, 48, "提示语管理工具"
  WScript.Quit 1
End If
On Error GoTo 0

For Each file In folder.Files
  If StrComp(fso.GetExtensionName(file.Name), "pyw", vbTextCompare) = 0 Then
    On Error Resume Next
    Set ts = file.OpenAsTextStream(1, 0)   ' 1=ForReading, 0=ASCII
    If Err.Number = 0 Then
      head = ts.Read(8192)
      ts.Close
      If InStr(head, foundMarker) > 0 Then
        target = file.Path
        Exit For
      End If
    Else
      Err.Clear
    End If
    On Error GoTo 0
  End If
Next

If target = "" Then
  MsgBox "未在当前文件夹找到提示语管理工具(.pyw 文件)。" & vbCrLf & _
         "请确认本启动器与“学习倒计时提示语管理工具.pyw”在同一文件夹。", _
         48, "提示语管理工具"
  WScript.Quit 1
End If

Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = dir
' 0 = 隐藏窗口(无控制台)；False = 不等待
sh.Run "pythonw.exe """ & target & """", 0, False
