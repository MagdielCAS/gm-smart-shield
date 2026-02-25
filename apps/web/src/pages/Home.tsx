export function Home() {
	return (
		<div className="flex flex-col items-center justify-center space-y-4 text-center">
			<h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl">
				Welcome to GM Smart Shield
			</h1>
			<p className="max-w-[700px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
				Your local-first AI assistant for tabletop RPG Game Masters.
			</p>
		</div>
	);
}
