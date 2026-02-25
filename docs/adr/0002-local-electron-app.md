# 2. Local Electron App

Date: 2024-05-22

## Status

Accepted

## Context

GM Smart Shield is a local-first application designed to assist Game Masters. It currently consists of a Python FastAPI backend and a React frontend. The application needs to process local files (PDFs, Markdown, etc.) to build a knowledge base.

Web browsers restrict direct access to the local file system for security reasons. While users can upload files via `<input type="file">`, this approach:
1.  Requires copying the file content into the browser memory and then sending it over HTTP to the backend, which is inefficient for large local files.
2.  Does not align with the "local-first" philosophy where the app should feel like a native desktop tool that can index folders or files in place (or via a simple path reference).
3.  We want to avoid unnecessary data transfer overhead when both the client and server are on the same machine.

## Decision

We will wrap the existing React frontend in an **Electron** application.

The architecture will be:
- **Backend**: The Python FastAPI server remains as is, running locally.
- **Frontend**: The React app will be served within an Electron window.
- **IPC (Inter-Process Communication)**: We will use Electron's IPC to handle system-level operations, specifically opening file dialogs to retrieve absolute file paths.
- **Data Flow**:
    1.  User clicks "Add Source" in the frontend.
    2.  Electron opens a native file dialog.
    3.  User selects a file.
    4.  Electron returns the *absolute path* of the file to the React app.
    5.  React app sends this *path* (string) to the Python backend API.
    6.  Python backend reads the file directly from the disk using the path.

This approach avoids uploading file content through the browser and allows the backend to efficiently process large files or directories directly.

## Consequences

### Positive
- **Native Experience**: Users get a standalone desktop application.
- **Performance**: Large files are processed directly by the backend without HTTP upload overhead.
- **Capabilities**: Access to native OS features (file system, menus, notifications) is now possible.

### Negative
- **Complexity**: Adds a build step and dependency on Electron.
- **Distribution**: Need to build and sign installers for different platforms (Windows, macOS, Linux).
- **Security**: Must ensure `nodeIntegration` is disabled and use `contextBridge` to expose only safe APIs to the renderer process.
