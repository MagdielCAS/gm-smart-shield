import React from "react";
import { cn } from "../../lib/utils";

interface GlassButtonProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant?: "primary" | "secondary" | "ghost" | "danger";
	size?: "sm" | "md" | "lg" | "icon";
}

export const GlassButton = React.forwardRef<
	HTMLButtonElement,
	GlassButtonProps
>(({ className, variant = "primary", size = "md", ...props }, ref) => {
	const variants = {
		primary:
			"bg-primary/90 text-primary-foreground hover:bg-primary shadow-lg hover:shadow-primary/20",
		secondary: "glass glass-hover text-foreground",
		ghost: "hover:bg-black/5 dark:hover:bg-white/5 text-foreground",
		danger:
			"bg-destructive/90 text-destructive-foreground hover:bg-destructive",
	};

	const sizes = {
		sm: "h-8 px-3 text-xs rounded-lg",
		md: "h-10 px-4 py-2 text-sm rounded-xl",
		lg: "h-12 px-6 text-base rounded-2xl",
		icon: "h-9 w-9 rounded-xl",
	};

	return (
		<button
			ref={ref}
			className={cn(
				"inline-flex items-center justify-center font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 active:scale-95",
				variants[variant],
				sizes[size],
				className,
			)}
			{...props}
		/>
	);
});
GlassButton.displayName = "GlassButton";
