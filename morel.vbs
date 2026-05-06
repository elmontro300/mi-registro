Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Users\Usuario\Documents\programas && streamlit run morel.py", 0
Set WshShell = Nothing