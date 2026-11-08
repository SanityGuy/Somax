# Somax Language Support for VS Code

This folder is a VS Code extension for `.smx` files. It provides:

- Somax language recognition
- TextMate syntax highlighting
- `##` line comments
- Automatic brackets, quotes, and indentation
- Code snippets for functions, conditions, loops, arrays, imports, and output
- `Somax: Run Current File` command
- Optional run-on-save
- A dedicated integrated terminal named `Somax`

## Requirements

- Visual Studio Code
- Python installed
- Somax 1.0 installed with `python -m pip install -e .`

The extension runs files using `python -m somax.main`, so the `somax.exe` Scripts PATH warning does not prevent execution.

## Install locally on Windows

1. Close VS Code.
2. Copy this entire `Somax-VSCode-Extension` folder into:

   `%USERPROFILE%\.vscode\extensions\somax.somax-language-0.1.0`

3. Open VS Code again.
4. Open a `.smx` file.

You can also run this PowerShell command from the parent directory containing this extension folder:

```powershell
$destination = "$env:USERPROFILE\.vscode\extensions\somax.somax-language-0.1.0"
New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
Copy-Item -Recurse -Force ".\Somax-VSCode-Extension" $destination
```

If VS Code does not recognize the extension, run `Developer: Reload Window` from the Command Palette.

## Use

- Open any `.smx` file.
- Press `Ctrl+Shift+P`.
- Run `Somax: Run Current File`.
- Or use the play icon in the editor title bar / right-click menu.

## Run on save

Open Settings and search for `Somax Run on Save`, or add this to `settings.json`:

```json
{
  "somax.runOnSave": true,
  "somax.pythonPath": "python",
  "somax.clearTerminalBeforeRun": true
}
```

Run-on-save is disabled by default to avoid unexpectedly executing every save.

If Python is invoked as `py` on your machine, change `somax.pythonPath` to `py`. An absolute Python executable path is also supported.

## Current scope

This first extension release provides syntax highlighting and execution integration. It does not yet provide a language server, autocomplete based on symbol analysis, go-to-definition, debugger integration, or compiler diagnostics. Those can be added in a later extension release.
