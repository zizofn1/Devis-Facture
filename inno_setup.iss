[Setup]
AppName=Devis-Facture F&Z
AppVersion=3.5
DefaultDirName=C:\Devis-Facture FZ
DefaultGroupName=Devis-Facture F&Z
OutputDir=dist
OutputBaseFilename=DevisFacture_Setup_v3.5
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\Devis-Facture F&Z.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Devis-Facture-FZ\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Devis-Facture F&Z"; Filename: "{app}\Devis-Facture F&Z.exe"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\Devis-Facture F&Z"; Filename: "{app}\Devis-Facture F&Z.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Dirs]
Name: "{app}"; Permissions: users-modify

[Run]
Filename: "{app}\Devis-Facture F&Z.exe"; Description: "{cm:LaunchProgram,Devis-Facture F&Z}"; Flags: nowait postinstall skipifsilent
