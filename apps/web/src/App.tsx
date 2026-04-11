import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, HashRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import ChatPage from "./pages/ChatPage";
import EncountersPage from "./pages/EncountersPage";
import { Home } from "./pages/Home";
import KnowledgePage from "./pages/KnowledgePage";
import NotesPage from "./pages/NotesPage";
import PlayerSheetPage from "./pages/PlayerSheetPage";
import ReferencesPage from "./pages/ReferencesPage";
import SheetDetailsPage from "./pages/SheetDetailsPage";
import SheetsPage from "./pages/SheetsPage";

const queryClient = new QueryClient();
const Router =
	window.location.protocol === "file:" ? HashRouter : BrowserRouter;

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<Router>
				<Routes>
					<Route path="/public/sheet/:id" element={<PlayerSheetPage />} />
					<Route path="/" element={<Layout />}>
						<Route index element={<Home />} />
						<Route path="knowledge" element={<KnowledgePage />} />
						<Route path="chat" element={<ChatPage />} />
						<Route path="notes" element={<NotesPage />} />
						<Route path="encounters" element={<EncountersPage />} />
						<Route path="references" element={<ReferencesPage />} />
						<Route path="sheets" element={<SheetsPage />} />
						<Route path="sheets/:id" element={<SheetDetailsPage />} />
					</Route>
				</Routes>
			</Router>
		</QueryClientProvider>
	);
}

export default App;
