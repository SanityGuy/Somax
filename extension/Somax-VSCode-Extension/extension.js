const vscode = require("vscode");
const path = require("path");

let outputChannel;
let runOnSaveEnabled;

function activate(context) {
    outputChannel = vscode.window.createOutputChannel("Somax");
    const config = vscode.workspace.getConfiguration("somax");
    runOnSaveEnabled = config.get("runOnSave", false);

    const runCommand = vscode.commands.registerCommand("somax.runFile", async (uri) => {
        const editor = vscode.window.activeTextEditor;
        const document = uri && uri.fsPath
            ? await vscode.workspace.openTextDocument(uri)
            : editor && editor.document;

        if (!document || document.languageId !== "somax") {
            vscode.window.showErrorMessage("Open a Somax (.smx) file first.");
            return;
        }

        if (document.isDirty) {
            const saved = await document.save();
            if (!saved) {
                vscode.window.showErrorMessage("Somax run cancelled because the file could not be saved.");
                return;
            }
        }

        const pythonPath = vscode.workspace.getConfiguration("somax").get("pythonPath", "python");
        const clearTerminal = vscode.workspace.getConfiguration("somax").get("clearTerminalBeforeRun", true);
        const terminal = getTerminal();
        terminal.show(true);

        if (clearTerminal) {
            terminal.sendText(process.platform === "win32" ? "cls" : "clear");
        }

        const filePath = document.uri.fsPath;
        terminal.sendText(`${quote(pythonPath)} -m somax.main ${quote(filePath)}`);
        outputChannel.appendLine(`Running ${filePath}`);
    });

    const toggleRunOnSave = vscode.commands.registerCommand("somax.toggleRunOnSave", async () => {
        runOnSaveEnabled = !runOnSaveEnabled;
        await vscode.workspace.getConfiguration("somax").update(
            "runOnSave",
            runOnSaveEnabled,
            vscode.ConfigurationTarget.Global
        );
        vscode.window.showInformationMessage(`Somax run on save ${runOnSaveEnabled ? "enabled" : "disabled"}.`);
    });

    const saveListener = vscode.workspace.onDidSaveTextDocument((document) => {
        if (runOnSaveEnabled && document.languageId === "somax") {
            vscode.commands.executeCommand("somax.runFile", document.uri);
        }
    });

    const configListener = vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration("somax.runOnSave")) {
            runOnSaveEnabled = vscode.workspace.getConfiguration("somax").get("runOnSave", false);
        }
    });

    context.subscriptions.push(runCommand, toggleRunOnSave, saveListener, configListener, outputChannel);
}

function getTerminal() {
    let terminal = vscode.window.terminals.find(item => item.name === "Somax");
    if (!terminal) {
        terminal = vscode.window.createTerminal({ name: "Somax" });
    }
    return terminal;
}

function quote(value) {
    const text = String(value);
    if (process.platform === "win32") {
        return `"${text.replace(/"/g, '\\"')}"`;
    }
    return `'${text.replace(/'/g, "'\\''")}'`;
}

function deactivate() {}

module.exports = { activate, deactivate };
