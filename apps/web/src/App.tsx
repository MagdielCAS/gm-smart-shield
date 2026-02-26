import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, HashRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import KnowledgePage from "./pages/KnowledgePage";

const queryClient = new QueryClient();
const Router =
	window.location.protocol === "file:" ? HashRouter : BrowserRouter;

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<Router>
				<Routes>
					<Route path="/" element={<Layout />}>
						<Route index element={<Home />} />
						<Route path="knowledge" element={<KnowledgePage />} />
					</Route>
				</Routes>
			</Router>
		</QueryClientProvider>
	);
}

export default App;
