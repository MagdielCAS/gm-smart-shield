export interface ElectronAPI {
	openFile: () => Promise<string | null>;
}

declare global {
	interface Window {
		electron: ElectronAPI;
	}
}
