Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\aurel\Desktop\social-dashboard"
WshShell.Run """C:\Users\aurel\Desktop\social-dashboard\run.bat""", 0, False
