import {
	BookMarked,
	BookOpen,
	FileBadge,
	FileText,
	Home,
	MessageSquare,
	Monitor,
	Moon,
	// Settings,
	Shield,
	Sun,
	Swords,
} from "lucide-react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { type Theme, useTheme } from "../lib/useTheme";
import { cn } from "../lib/utils";
import { SFIcon } from "./ui/SFIcon";

const themeOptions: { value: Theme; icon: typeof Sun; label: string }[] = [
	{ value: "light", icon: Sun, label: "Light" },
	{ value: "system", icon: Monitor, label: "System" },
	{ value: "dark", icon: Moon, label: "Dark" },
];

export function Layout() {
	const location = useLocation();
	const { theme, setTheme } = useTheme();

	const navItems = [
		{ href: "/", label: "Dashboard", icon: Home },
		{ href: "/knowledge", label: "Knowledge", icon: BookOpen },
		{ href: "/notes", label: "Notes", icon: FileText },
		{ href: "/encounters", label: "Encounters", icon: Swords },
		{ href: "/references", label: "References", icon: BookMarked },
		{ href: "/sheets", label: "Sheets", icon: FileBadge },
		{ href: "/chat", label: "AI Chat", icon: MessageSquare },
	];

	return (
		<div className="flex h-screen w-full bg-background mesh-gradient-bg overflow-hidden text-foreground">
			{/* Glass Sidebar */}
			<aside className="hidden w-64 flex-col border-r border-white/20 bg-white/50 dark:bg-black/30 backdrop-blur-xl md:flex z-20 shadow-xl">
				<div className="flex h-16 items-center px-6 border-b border-white/10">
					<Link to="/" className="flex items-center gap-2 font-semibold">
						<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white shadow-lg shadow-primary/30">
							<SFIcon icon={Shield} className="h-5 w-5" />
						</div>
						<span className="text-lg tracking-tight">GM Shield</span>
					</Link>
				</div>
				<nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
					{navItems.map((item) => {
						const isActive = location.pathname === item.href;
						return (
							<Link
								key={item.href}
								to={item.href}
								className={cn(
									"flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
									isActive
										? "bg-white/80 dark:bg-white/10 text-primary shadow-sm ring-1 ring-black/5"
										: "text-muted-foreground hover:bg-white/40 dark:hover:bg-white/10 hover:text-foreground",
								)}
							>
								<SFIcon
									icon={item.icon}
									className={cn("h-5 w-5", isActive ? "stroke-[2]" : "")}
								/>
								{item.label}
							</Link>
						);
					})}
				</nav>
				<div className="p-4 border-t border-white/10 space-y-3">
					{/* Theme Switcher */}
					<div className="rounded-xl bg-white/30 dark:bg-white/5 p-1 flex items-center gap-0.5">
						{themeOptions.map(({ value, icon: Icon, label }) => (
							<button
								key={value}
								type="button"
								aria-label={`${label} theme`}
								title={`${label} theme`}
								onClick={() => setTheme(value)}
								className={cn(
									"flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium transition-all duration-200",
									theme === value
										? "bg-white dark:bg-white/20 text-foreground shadow-sm"
										: "text-muted-foreground hover:text-foreground",
								)}
							>
								<Icon className="h-3.5 w-3.5" />
								{label}
							</button>
						))}
					</div>

					{/* System Status */}
					<div className="rounded-xl bg-white/30 dark:bg-white/5 p-4 backdrop-blur-md">
						<p className="text-xs font-medium text-muted-foreground">
							System Status
						</p>
						<div className="mt-2 flex items-center gap-2">
							<span className="relative flex h-2 w-2">
								<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
								<span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
							</span>
							<span className="text-xs font-medium text-foreground">
								Online
							</span>
						</div>
					</div>
				</div>
			</aside>

			{/* Main Content Area */}
			<div className="flex flex-1 flex-col overflow-hidden relative z-10">
				{/* Top Header (Glass) */}
				<header className="flex h-16 items-center justify-between border-b border-white/20 bg-white/30 dark:bg-black/20 px-6 backdrop-blur-xl supports-[backdrop-filter]:bg-white/10">
					<div className="flex items-center gap-4">
						<h1 className="text-lg font-semibold text-foreground">
							{navItems.find((n) => n.href === location.pathname)?.label ||
								"Dashboard"}
						</h1>
					</div>
					<div className="flex items-center gap-4">
						<div className="h-8 w-8 rounded-full bg-gradient-to-tr from-blue-400 to-purple-500 shadow-inner ring-2 ring-white/50" />
					</div>
				</header>

				{/* Scrollable Content */}
				<main className="flex-1 overflow-y-auto p-6 md:p-8">
					<div className="mx-auto max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500 h-full">
						<Outlet />
					</div>
				</main>
			</div>
		</div>
	);
}
