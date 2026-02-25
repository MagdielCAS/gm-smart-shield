import { Link, Outlet } from "react-router-dom";

export function Layout() {
	return (
		<div className="min-h-screen bg-background font-sans antialiased">
			<header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
				<div className="container flex h-14 items-center px-4">
					<div className="mr-4 hidden md:flex">
						<Link to="/" className="mr-6 flex items-center space-x-2">
							<span className="hidden font-bold sm:inline-block">
								GM Smart Shield
							</span>
						</Link>
					</div>
				</div>
			</header>
			<main className="container px-4 py-6 md:py-12">
				<Outlet />
			</main>
		</div>
	);
}
