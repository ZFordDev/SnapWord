#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{5B897A3D-7F0E-4C98-9D52-9288EBB3FDAB}
AppName=SnapWord
AppVersion={#AppVersion}
AppVerName=SnapWord {#AppVersion}
AppPublisher=ZFordDev
DefaultDirName={localappdata}\Programs\SnapWord
DefaultGroupName=SnapWord
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\snapword.exe
SetupIconFile=..\snapword\assets\logo.ico
OutputBaseFilename=snapword-v{#AppVersion}-windows-x86_64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\snapword.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SnapWord"; Filename: "{app}\snapword.exe"
Name: "{autodesktop}\SnapWord"; Filename: "{app}\snapword.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\snapword.exe"; Description: "Launch SnapWord"; Flags: postinstall nowait skipifsilent
