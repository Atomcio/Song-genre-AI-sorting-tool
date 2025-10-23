Set WshShell = CreateObject("WScript.Shell")
Set oShellLink = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\Music Genre Sorter.lnk")

' Ścieżka do pliku bat
currentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
oShellLink.TargetPath = currentDir & "\uruchom_music_sorter.bat"
oShellLink.WorkingDirectory = currentDir
oShellLink.Description = "Music Genre Sorter - ChatGPT Edition"
oShellLink.IconLocation = "shell32.dll,13"

oShellLink.Save

WScript.Echo "Skrót 'Music Genre Sorter' został utworzony na pulpicie!"