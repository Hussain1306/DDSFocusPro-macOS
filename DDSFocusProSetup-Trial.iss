[Setup]
AppName=DDS FocusPro Trial
AppVersion=1.7.1
DefaultDirName={localappdata}\DDSFocusPro-Trial
DefaultGroupName=DDS FocusPro Trial
OutputDir=releases\v1.7
OutputBaseFilename=DDSFocusProSetup-Trial-v1.7.1
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest 
SetupIconFile=icon.ico 

[Files]
; Main executables (with embedded icons)
Source: "dist\DDSFocusPro-Trial.exe"; DestDir: "{app}"; DestName: "DDSFocusPro-Trial.exe"; Flags: ignoreversion
Source: "dist\connector-trial.exe"; DestDir: "{app}"; DestName: "connector.exe"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; Essential Flask application folders (now in same directory)
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration files (now in same directory)
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: "themes.json"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Only create essential directories
Name: "{app}\data"
Name: "{app}\logs"
Name: "{app}\output"

[Icons]
Name: "{group}\DDS FocusPro Trial"; Filename: "{app}\DDSFocusPro-Trial.exe"; IconFilename: "{app}\icon.ico"
Name: "{userdesktop}\DDS FocusPro Trial"; Filename: "{app}\DDSFocusPro-Trial.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
; Optional: Run the application after installation
Filename: "{app}\DDSFocusPro-Trial.exe"; Description: "Launch DDS FocusPro Trial"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up application data on uninstall
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\output"

[Code]
// No additional code needed
