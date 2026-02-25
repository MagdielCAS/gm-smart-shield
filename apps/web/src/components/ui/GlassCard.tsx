import React from "react";
import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
	({ className, children, ...props }, ref) => {
		return (
			<div
				ref={ref}
				className={cn(
					"glass rounded-3xl p-6 transition-all duration-300",
					className,
				)}
				{...props}
			>
				{children}
			</div>
		);
	},
);
GlassCard.displayName = "GlassCard";
